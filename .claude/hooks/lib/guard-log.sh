#!/usr/bin/env bash
# Append one guard firing to the guard event log.
#
# This is the only new capture the session provenance design calls for. A rule
# that is merely in force leaves no trace, and whether a rule was followed is
# not observable at all, but a guard that blocks a tool call is a real event
# with a real outcome. Logging it is what turns "rules enforced" into something
# that can be joined to a session and counted.
#
# The record carries the session id and the tool that was blocked, so it joins
# to a transcript on session_id and to one turn on tool_name plus timestamp.
#
# Shape, one JSON object per line:
#   {"event":"guard-fired","guard":...,"rule":...,"decision":"deny",
#    "detail":...,"session_id":...,"tool_name":...,"tool_use_id":...,
#    "tool_name_reason":...,"capability":...,"runtime":...,"cwd":...,
#    "timestamp":...}
#
# tool_use_id is the payload's own id for the denied call, empty when the
# payload carries none. It is how a counter that reserved a slot for a call at
# PreToolUse learns that a sibling hook denied it (G-02 of
# docs/adr/2026-09-23-close-the-gaps-the-fixes-surfaced.md): hooks/lib/tool-budget.py
# and hooks/subagent-cap-guard.sh release the reservation it names.
#
# Usage, from inside a guard's deny path:
#   source "$HOOK_DIR/lib/guard-log.sh"
#   guard_log_event prose-guard no-em-dash deny "$label" "$payload"
#
# Contract:
# - Fail open, always. A logging failure must never change a guard's decision,
#   so every step is guarded and the function always returns 0.
# - Never on the happy path. The payload is only parsed when a guard actually
#   fires, so a passing tool call pays nothing for this.
# - Redacted. detail passes through ss_redact and is capped, because a guard's
#   label can quote the text it rejected.
#
# Field notes (2026-09-21 finding, WI-16/F-21):
# - tool_name is read from the payload's own top-level "tool_name" key on
#   every runtime this repo deploys to. Verified directly against each
#   runtime's own hook documentation: Claude Code, OpenCode
#   (hooks/opencode-runtime-hooks.ts payload()), Codex
#   (developers.openai.com/codex/hooks, redirects to
#   learn.chatgpt.com/docs/hooks), Gemini CLI (geminicli.com/docs/hooks/reference),
#   and Cursor (cursor.com/docs/hooks) all name the tool under "tool_name" at
#   the top level. No runtime carries the tool name under a different key, so
#   no alias mapping exists here; inventing one would be a guess, not a fix.
#   When tool_name is genuinely absent from the payload, tool_name_reason
#   carries a short reason instead of leaving the field silently empty.
# - session_id has one verified alias: Cursor's hook payload names the join
#   key "conversation_id" instead of "session_id" (cursor.com/docs/hooks).
#   session_id falls back to conversation_id when session_id itself is absent.
# - capability names the skill, agent, or command in effect, when the payload
#   exposes one: a subagent call's tool_input.subagent_type (the tool is
#   "Agent" on Claude Code 2.1.280, docs/runtimes/evidence/
#   claude-code-2.1.280-subagent-pretooluse.json, and "Task" before), a Skill's
#   tool_input.skill, a SlashCommand's tool_input.command, or a top-level
#   agent_type field. Empty when none of those are present.
# - runtime is inferred from where this file itself was deployed (the same
#   technique hooks/prompt-capture.sh uses for its own runtime label), or
#   taken from GUARD_LOG_RUNTIME when a caller sets it (tests use this to
#   exercise a shape without needing a real deployment path).
#
# Env: GUARD_LOG_DISABLE=1 turns it off.
#      GUARD_LOG_DIR overrides the directory (default ~/.agent-hooks/telemetry).
#      GUARD_LOG_RUNTIME overrides the inferred runtime label.

set -u

GUARD_LOG_DETAIL_CAP="${GUARD_LOG_DETAIL_CAP:-160}"

# _guard_log_infer_runtime: the runtime label for wherever this file itself
# was deployed, mirroring hooks/prompt-capture.sh's own inference from its
# deployed path. Prints nothing when the path matches no known runtime
# directory (for instance, running straight from the source tree).
_guard_log_infer_runtime() {
  case "${BASH_SOURCE[0]}" in
    */.codex/*) printf 'codex' ;;
    */.gemini/*) printf 'gemini' ;;
    */.cursor/*) printf 'cursor' ;;
    */.config/opencode/*) printf 'opencode' ;;
    */.claude/*) printf 'claude' ;;
    *) printf '' ;;
  esac
}

guard_log_event() {
  [ "${GUARD_LOG_DISABLE:-0}" = "1" ] && return 0
  [ "${RUNTIME_HOOKS_DISABLE:-0}" = "1" ] && return 0

  local guard="${1:-unknown}"
  local rule="${2:-}"
  local decision="${3:-deny}"
  local detail="${4:-}"
  local payload="${5:-}"

  command -v python3 >/dev/null 2>&1 || return 0

  local dir="${GUARD_LOG_DIR:-${HOME:-/tmp}/.agent-hooks/telemetry}"
  mkdir -p "$dir" 2>/dev/null || return 0
  local file="$dir/guard-events-$(date -u '+%Y-%m-%d').jsonl"
  local runtime="${GUARD_LOG_RUNTIME:-$(_guard_log_infer_runtime)}"

  # A guard label can quote the rejected text, so redact before it is stored.
  if command -v ss_redact >/dev/null 2>&1; then
    detail="$(ss_redact "$detail" 2>/dev/null || printf '%s' "$detail")"
  fi
  detail="$(printf '%s' "$detail" | tr -d '\000-\010\013\014\016-\037' | cut -c "1-$GUARD_LOG_DETAIL_CAP")"

  # The assignments belong to python3, not to printf. Placing them before the
  # pipe would set them for the left side only, and the record would be blank.
  printf '%s' "$payload" | \
    GUARD_LOG_GUARD="$guard" \
    GUARD_LOG_RULE="$rule" \
    GUARD_LOG_DECISION="$decision" \
    GUARD_LOG_DETAIL="$detail" \
    GUARD_LOG_FILE="$file" \
    GUARD_LOG_RUNTIME_RESOLVED="$runtime" \
    python3 -c '
import datetime, json, os, sys

try:
    raw = sys.stdin.read()
except Exception:
    raw = ""
try:
    payload = json.loads(raw) if raw.strip() else {}
except Exception:
    payload = {}
if not isinstance(payload, dict):
    payload = {}

tool_name = payload.get("tool_name") or ""
tool_name_reason = "" if tool_name else "tool_name absent from payload"

session_id = payload.get("session_id") or payload.get("conversation_id") or ""

tool_use_id = payload.get("tool_use_id") or ""
if not isinstance(tool_use_id, str):
    tool_use_id = ""

tool_input = payload.get("tool_input")
if not isinstance(tool_input, dict):
    tool_input = {}
capability = payload.get("agent_type") or ""
if not capability:
    if tool_name in ("Task", "Agent"):
        capability = tool_input.get("subagent_type") or ""
    elif tool_name == "Skill":
        capability = tool_input.get("skill") or ""
    elif tool_name == "SlashCommand":
        capability = tool_input.get("command") or ""
if not isinstance(capability, str):
    capability = ""

record = {
    "event": "guard-fired",
    "guard": os.environ.get("GUARD_LOG_GUARD", ""),
    "rule": os.environ.get("GUARD_LOG_RULE", ""),
    "decision": os.environ.get("GUARD_LOG_DECISION", ""),
    "detail": os.environ.get("GUARD_LOG_DETAIL", ""),
    "session_id": session_id,
    "tool_name": tool_name,
    "tool_use_id": tool_use_id,
    "tool_name_reason": tool_name_reason,
    "capability": capability,
    "runtime": os.environ.get("GUARD_LOG_RUNTIME_RESOLVED", ""),
    "cwd": payload.get("cwd") or "",
    "timestamp": datetime.datetime.now(datetime.timezone.utc)
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z"),
}
try:
    with open(os.environ["GUARD_LOG_FILE"], "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
except Exception:
    pass
' 2>/dev/null || true

  return 0
}
