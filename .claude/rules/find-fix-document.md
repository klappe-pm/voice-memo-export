# find-fix-document

## binding

When work surfaces a bug, the unit of delivery is find, document, fix. All three, in that order, in the same cycle that found it. A bug that is found and mentioned but not written down is lost the moment the session ends. A bug that is fixed without being written down teaches nobody why the code now looks the way it does.

This applies to any defect the work trips over, not only defects in the thing being changed. Incidental bugs are the ones most likely to be silently skipped, and they are the ones nobody is looking for.

## the-three-steps

**Find.** Verify the defect before calling it one. Run the failing case and read the real output. A linter's complaint, another agent's report, or a plausible-looking code path is a hypothesis, not a finding. Confirm it independently: if a validator says the YAML is invalid, parse the YAML yourself; if a function looks unreachable, call it and watch it not fire. Roughly half of what looks like a bug is a schema disagreement or a wrong assumption in the reporting tool.

**Document.** Write the finding where the next person will hit it, before fixing it. The record states what breaks, the evidence that it breaks, and the blast radius. Verbatim output beats description. If the fix lands in the same change, the commit message and PR body carry the record; if it does not, it goes to the project's record: a defect to a bug record under `docs/bugs/` paired with a GitHub issue, a decision to an ADR under `docs/adr/`, an input that is neither to a note under `docs/ideas/` that a later ADR picks up, each with enough detail to act on cold, and the blocker is named.

**Fix.** Correct the cause, not the symptom. Add the test that fails without the fix and passes with it, then prove it by reverting the fix and watching the test fail. A test that passes in both states documents nothing and guards nothing.

## when-the-fix-cannot-land-now

Some defects are genuinely out of scope: they need a decision, they are blocked on a guard or a merge, or fixing them would balloon an unrelated change. That is a reason to defer the fix, never a reason to skip the record.

Deferring means: the finding is written to `docs/bugs/` with its evidence and its blocker and a GitHub issue that tracks it, the user is told in the same turn, and the work continues. Silently carrying a known defect forward is the failure this rule exists to prevent. So is fixing an unrelated bug inside a change whose reviewers are not expecting it; when in doubt, record it and ship it separately.

## scope-discipline

Finding a bug does not authorize expanding the task. Fix what is in the change's blast radius, record the rest. A defect that predates the change and does not affect it gets a bug record and its issue, not an opportunistic edit that makes the diff harder to review.

The exception is a defect the current change would otherwise leave broken: a dangling reference the change created, a test the change invalidated, a contract the change violated. Those are part of the change, not follow-up work.
