#!/usr/bin/env bash
# PreToolUse hook. Hard deny on agent authorship attribution in authored
# content, commit messages, and published GitHub text.
#
# The user's standing rule (rules/no-agent-attribution.md) is that nothing
# authored on their behalf credits a coding agent. Runtime system prompts push
# the opposite way: they append a co-author trailer to every commit, a
# "generated with" footer to every pull request body, and a session permalink
# under both. A text rule loses that argument every time; this hook makes the
# attribution impossible to write.
#
# Registered once in hooks/hooks.json with no matcher, so it runs on every
# tool call (A-03 of
# docs/adr/2026-09-23-make-attribution-enforcement-travel-with-the-repository.md):
# a GitHub writer from any MCP server reaches it, not only mcp__github__.
#
# Scope of the deny, by tool:
#   - Write, Edit, NotebookEdit: the authored content fields.
#   - Bash: the command text, but only for a command that publishes authored
#     text (git commit, git tag, gh pr, gh issue, and friends), so grepping for
#     an attribution string is not itself a violation. A file the command names
#     as its body (gh --body-file, -F body=@<path>, --field body=@<path>,
#     git commit -F or --file) is read and scanned with it; a file that cannot
#     be read is scanned as absent.
#   - Any other tool: the message-shaped fields of the tool input, so a pull
#     request body or issue comment is covered. A tool with no such field
#     passes after one detector run.
#
# Detection lives in hooks/lib/attribution-detect.py, shared with the git
# commit-msg backstop scripts/git-hooks/strip-commit-attribution.sh, which
# strips the same lines out of a message written with plain git.
#
# One exemption, from rules/docs-provenance-frontmatter.md: a session link on
# a `session-link:` frontmatter line is provenance metadata, and the detector
# passes it. The same link on any other line is still denied, and the
# commit-msg backstop still strips it.
#
# Escape hatch: set ALLOW_AGENT_ATTRIBUTION=1 in the session environment for
# the rare legitimate case (quoting a third party's commit trailer verbatim,
# importing a fixture, writing this guard's own tests).
#
# Emits a single JSON object on stdout per Claude Code's hook protocol.

set -euo pipefail
[ "${RUNTIME_HOOKS_DISABLE:-0}" = "1" ] && exit 0
[ "${ALLOW_AGENT_ATTRIBUTION:-0}" = "1" ] && exit 0

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Carried copy (WI-53). scripts/sync-projects.py carries this file and its
# library into every active project's tracked .claude/hooks/ and registers it
# there, so the guard travels with a clone. On a machine that also has the
# user-level guard, Claude Code runs both registrations for the same call, in
# parallel and with no shared state, so "the other one already ran" cannot be
# observed. The decision would be the same, but every deny would be logged
# twice and double counted by the session ledger. So the carried copy, and
# only the carried copy (this file running from $CLAUDE_PROJECT_DIR/.claude/
# hooks), stands down when the user-level guard is registered in
# ~/.claude/settings.json and is byte identical, library included: that guard
# decides this call with this code. If either differs, or HOME has no guard
# (a container, a fresh clone elsewhere), the carried copy decides itself.
_carried_copy_defers() {
  [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -n "${HOME:-}" ] || return 1
  local here project_hooks user_hooks rel
  here="$(cd "$HOOK_DIR" && pwd -P)" || return 1
  project_hooks="$(cd "$CLAUDE_PROJECT_DIR/.claude/hooks" 2>/dev/null && pwd -P)" || return 1
  [ "$here" = "$project_hooks" ] || return 1
  user_hooks="$(cd "$HOME/.claude/hooks" 2>/dev/null && pwd -P)" || return 1
  [ "$user_hooks" != "$here" ] || return 1
  # A registered guard that cannot execute never decides the call.
  [ -x "$user_hooks/no-attribution-guard.sh" ] || return 1
  # Registered means a PreToolUse group that matches every tool (no matcher,
  # "" or "*") and runs the user-level guard; a mention anywhere else, a
  # PostToolUse entry or a narrower matcher does not cover this call.
  python3 -c '
import json, os, sys
try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        data = json.load(handle)
except Exception:
    sys.exit(1)
home = os.environ.get("HOME", "")
tail = "/.claude/hooks/no-attribution-guard.sh"
targets = {"$HOME" + tail, "${HOME}" + tail, "~" + tail, home + tail}
hooks = data.get("hooks") if isinstance(data, dict) else None
groups = hooks.get("PreToolUse") if isinstance(hooks, dict) else None
for group in groups if isinstance(groups, list) else []:
    if not isinstance(group, dict) or (group.get("matcher") or "") not in ("", "*"):
        continue
    for hook in group.get("hooks") or []:
        if isinstance(hook, dict) and str(hook.get("command", "")).strip().strip("\"") in targets:
            sys.exit(0)
sys.exit(1)
' "$HOME/.claude/settings.json" 2>/dev/null || return 1
  for rel in no-attribution-guard.sh lib/log.sh lib/guard-utils.sh lib/guard-log.sh lib/attribution-detect.py; do
    cmp -s "$here/$rel" "$user_hooks/$rel" || return 1
  done
  return 0
}
_carried_copy_defers && exit 0
# shellcheck source=lib/log.sh
source "$HOOK_DIR/lib/log.sh"
# shellcheck source=lib/guard-log.sh
[ -f "$HOOK_DIR/lib/guard-log.sh" ] && source "$HOOK_DIR/lib/guard-log.sh"
command -v guard_log_event >/dev/null 2>&1 || guard_log_event() { :; }

payload="$(cat)"
[ -n "$payload" ] || exit 0

label="$(printf '%s' "$payload" | python3 "$HOOK_DIR/lib/attribution-detect.py" detect-payload 2>/dev/null || true)"

if [ -n "$label" ]; then
  msg="Agent attribution in authored content ($label). The no-agent-attribution rule is absolute (rules/no-agent-attribution.md): commit messages, pull request and issue bodies, code comments, and documents carry no co-author trailer naming a model, no 'generated with' footer, no session permalink, and no robot byline. Remove those lines and retry; keep the human author only. (Set ALLOW_AGENT_ATTRIBUTION=1 only to quote a third party's text verbatim.)"
  log_warn "no-attribution-guard: denied write ($label)"
  guard_log_event no-attribution-guard no-agent-attribution deny "$label" "$payload"
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' \
    "$(printf '%s' "$msg" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
  exit 0
fi

exit 0
