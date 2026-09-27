#!/usr/bin/env bash
# PreToolUse hook. Hard deny on a shell command that prints a process, shell
# or launchd environment.
#
# rules/no-secret-exposure.md forbids reading raw env output into context,
# because an environment holds live keys. Until this hook, nothing enforced
# it: on 2026-09-26 a diagnostic `launchctl print gui/501/<label>` printed six
# provider keys from the launchd global environment into a session transcript
# (docs/bugs/launchctl-print-exposed-launchd-environment-keys.md; the same
# class as WI-100 in PLAN.md).
#
# Registered once in hooks/hooks.json with no matcher, because the shell tool
# has a different name on each runtime (Bash on Claude Code and Codex,
# run_shell_command on Gemini CLI, Shell on Cursor) and the Gemini adapter
# passes a matcher through untranslated. The detector judges any tool input
# that carries a command (Monitor and MCP process tools run shell commands
# too); every other payload passes. A payload with no "command" or "cmd"
# field exits before any interpreter starts.
#
# Detection lives in hooks/lib/env-dump-detect.py, which splits a compound
# command into simple commands and looks through bash -c, ssh, railway ssh,
# sudo, env VAR=val and the other wrappers that run a command.
#
# Escape hatch: ALLOW_ENV_DUMP=1 in the session environment, and only with the
# operator's explicit approval in the current session
# (rules/guard-bypass-approval.md). An environment dump is never needed to
# answer "is this job running" or "is this variable set".
#
# Emits a single JSON object on stdout per Claude Code's hook protocol.

set -euo pipefail
[ "${RUNTIME_HOOKS_DISABLE:-0}" = "1" ] && exit 0
[ "${ALLOW_ENV_DUMP:-0}" = "1" ] && exit 0

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Carried copy, as for no-attribution-guard.sh (WI-53): scripts/sync-projects.py
# carries this file and its library into every active project's tracked
# .claude/hooks/ and registers it there. The carried copy stands down when the
# user-level guard is registered in ~/.claude/settings.json for every tool and
# is byte identical, library included, so one call is not judged and logged
# twice. If either differs, or HOME has no guard, the carried copy decides.
_carried_copy_defers() {
  [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -n "${HOME:-}" ] || return 1
  local here project_hooks user_hooks rel
  here="$(cd "$HOOK_DIR" && pwd -P)" || return 1
  project_hooks="$(cd "$CLAUDE_PROJECT_DIR/.claude/hooks" 2>/dev/null && pwd -P)" || return 1
  [ "$here" = "$project_hooks" ] || return 1
  user_hooks="$(cd "$HOME/.claude/hooks" 2>/dev/null && pwd -P)" || return 1
  [ "$user_hooks" != "$here" ] || return 1
  [ -x "$user_hooks/env-dump-guard.sh" ] || return 1
  [ -f "$HOME/.claude/settings.json" ] || return 1
  python3 -c '
import json, os, sys
try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        data = json.load(handle)
except Exception:
    sys.exit(1)
home = os.environ.get("HOME", "")
tail = "/.claude/hooks/env-dump-guard.sh"
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
  for rel in env-dump-guard.sh lib/log.sh lib/guard-utils.sh lib/guard-log.sh lib/env-dump-detect.py; do
    cmp -s "$here/$rel" "$user_hooks/$rel" || return 1
  done
  return 0
}

payload="$(cat)"
[ -n "$payload" ] || exit 0
case "$payload" in
  *'"command"'* | *'"cmd"'*) ;;
  *) exit 0 ;;
esac

label="$(printf '%s' "$payload" | python3 "$HOOK_DIR/lib/env-dump-detect.py" detect-payload 2>/dev/null || true)"
[ -n "$label" ] || exit 0

# An allow writes nothing, so judging a call twice is harmless; only a deny
# is logged, so the carried copy's stand-down check and the log libraries
# are needed only here, which keeps them off every allowed shell call.
_carried_copy_defers && exit 0
# shellcheck source=lib/log.sh
source "$HOOK_DIR/lib/log.sh"
# shellcheck source=lib/guard-log.sh
[ -f "$HOOK_DIR/lib/guard-log.sh" ] && source "$HOOK_DIR/lib/guard-log.sh"
command -v guard_log_event >/dev/null 2>&1 || guard_log_event() { :; }

msg="Environment dump denied ($label). rules/no-secret-exposure.md forbids printing a process, shell or launchd environment, because it carries every live key into the transcript. Ask the narrow question instead: whether a launchd job is loaded, 'launchctl list | grep <label>'; whether a service is up, 'python3 scripts/components.py --services'; whether a variable is set, '[ -n \"\${VAR+x}\" ] && echo set' (existence, never the value); which Railway variables exist, their names in the Railway dashboard ('railway variables --kv' still prints values). Set ALLOW_ENV_DUMP=1 only with the operator's explicit approval in this session (rules/guard-bypass-approval.md)."
log_warn "env-dump-guard: denied command ($label)"
guard_log_event env-dump-guard no-secret-exposure deny "$label" "$payload"
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' \
  "$(printf '%s' "$msg" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
exit 0
