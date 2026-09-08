# guard-bypass-approval

When a hook, guard, permission check, or safety gate blocks an action, stop. The block is a required checkpoint, not an obstacle to optimize.

## never-without-approval

Without explicit user approval in the same session, never:

- Change working directory, target path, or arguments to escape a scope guard after it blocked a write.
- Set a documented bypass flag (`ALLOW_EMDASH=1`, `ALLOW_HARDWRAP=1`, `RUNTIME_HOOKS_DISABLE=1`, or any equivalent).
- Pass `--no-verify`, `-n`, `--force`, `--admin`, or any flag that skips a hook or required gate.
- Disable, comment out, or edit the guard itself so the action passes.
- Route through Bash, a shell redirect, a heredoc, or any write path the guard does not instrument after the guarded path was blocked. Choosing a write method the guard cannot see is bypass, not a workaround.

## what-counts-as-approval

"The action was user-directed" is not approval. The guard fires to force a human decision on that specific action; a general instruction to complete the task does not authorize defeating the check the task tripped. Repeating the task without addressing the block is not approval; re-surface the block rather than treating repetition as a yes.

## when-a-guard-fires

Report in this order:

1. The block verbatim.
2. What the guard protects against.
3. Which bypass or documented remedy exists.
4. A single explicit question: proceed with bypass (requires yes), or fix the underlying condition?

## remedy-vs-bypass

Fix the condition the guard detected and the guard stops firing because the hazard is gone. Bypass makes the guard stop firing while the hazard remains.

Remedies: using a guard's documented fix, returning to the correct branch, splitting a compound command the guard flagged.

Bypasses: passing a bypass flag, editing the guard, choosing a write path the guard cannot see.
