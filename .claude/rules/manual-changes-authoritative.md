# manual-changes-authoritative

A change the user makes by hand is tracked, intentional, and accurate. It is the current state of record, not an anomaly to investigate. This applies to edits, deletions, renames, moves, reverts, and manual overrides of anything an agent generated.

## the-requirement

Treat the manual change as settled and proceed to the next action. Do not re-verify that it was intended. Do not audit whether it was complete, consistent, or correct. Do not surface it as a discrepancy, a regression, or an unexplained difference. Never offer, propose, or move toward undoing, restoring, or reverting it.

When a manual change contradicts an earlier plan, an audit finding, a generated artifact, or an agent's own prior output, the manual change wins. The other side is what gets updated to match, without asking whether the user meant it.

State the resulting factual state once, briefly, then continue. A second confirmation pass over the user's own deliberate action is the failure this rule exists to prevent.

## what-still-gets-reported

Report a downstream consequence only when it blocks the task in hand: a reference the change left dangling, a dependency that can no longer resolve, a command that will now fail. Report it once, as a fact to act on, never as grounds to reconsider the change or as an invitation to roll it back.

Restoration, rollback, and undo happen only when the user explicitly asks for them. "The change looks incomplete" is not a reason to restore, and neither is an agent's earlier analysis suggesting the files were still in use.

## scope-boundary

This rule governs the user's own changes. It does not relax `find-fix-document`, which still applies in full to defects the agent's own work introduces or trips over. An agent's bug is found, documented, and fixed. A user's edit is accepted.

It also does not license skipping a confirmation the user asked for, or acting on an ambiguous instruction without checking. The rule is about not re-litigating a change already made, not about reducing care before making one.
