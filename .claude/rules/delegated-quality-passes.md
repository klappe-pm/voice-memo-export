# delegated-quality-passes

## binding

Every agent that delivers a change, on every runtime and model, delegates quality passes to parallel subagents before the change is done: correctness (bugs, silent failures), tests (each test fails without its fix), cleanup (duplication, dead code) and speed (needless work in hot paths). Passes only report findings; a pass that must mutate code, such as reverting a fix, works in its own isolated worktree. The builder applies each finding with a failing test first or refutes it with evidence. A documentation-only change needs only the correctness pass. Passes stay within the change's files, the subagent cap and the budget.

## the-passes

- Correctness: read the diff against its record and plan row, hunt logic errors, unhandled errors, swallowed failures and wrong fallbacks, and reproduce each suspected bug before reporting it, per `find-fix-document`.
- Tests: for each new or changed test, name the mutation of the code it would catch, and revert the fix to watch it fail, in the pass's own isolated worktree so the builder's tree never moves under it; a test that passes both ways is a finding.
- Cleanup: report duplication, dead branches, unused code and needless indirection in the changed files, for the builder to remove with behavior identical and the surrounding code's idiom kept.
- Speed: find repeated reads, quadratic loops, unbounded scans, blocking calls in hooks and serial work that could run in parallel; measure before and after when a change is claimed faster.

## how-to-delegate

A runtime with subagents dispatches each pass as its own subagent with the diff, the files and the record, and asks for findings in a structured form; Claude Code uses its agent tool or a workflow, and Codex uses its subagents where the runtime supports them. A runtime without subagents runs the passes itself, one after another, and says so in the handoff. The builder that owns the change folds the findings in; a pass never edits files outside the change. Where a project hands review findings to a separate fixer, that fixer runs the same passes in each fix round.

## what-it-does-not-change

The passes do not replace the gates, the review or the handoff; they run before the pull request is opened and again inside each fix round. They never widen scope: a defect found outside the change is recorded under `find-fix-document`, not fixed in place. `hooks/subagent-cap-guard.sh` and the session's budget still bound how many subagents run.

## enforcement

No hook enforces this rule. The handoff's `Gates` field names each pass that ran and its result, which is how a reviewer checks it.
