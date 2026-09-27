# finish-or-record-scope-change

## binding

Work an agent decided not to do is a scope change. It is finished in the same cycle, or it is recorded as a scope change with its reason and its cost. It is never handed back as a closing list of things that were within reach and were skipped.

The failure this prevents has a recognisable shape: a report that ends "two things I did not do", naming work the agent understood, had the access to complete, and left undone because the turn felt finished. Nobody decided to drop that work. It was dropped, then described. Describing it is not the same as deciding it, and a list in a final message is where it stops being tracked.

## the-requirement

If the remaining work is reachable, do it before reporting. Reachable means the agent knows what the change is, knows where it goes, and can verify it with the tools already in hand. A turn ending is not a reason to stop, and neither is the work being smaller or less interesting than what came before.

An enumeration of undone work is not a deliverable. Producing one costs the user a decision they did not ask to make, about work they already asked for.

## what-is-genuinely-not-reachable

Some work legitimately cannot land now: it needs a decision only the user can make, it is blocked on a guard or a merge, the change would be unsafe without review, or completing it would expand a diff its reviewers are not expecting. Those are real reasons to stop, and each one names a specific blocker.

"I ran out of turn", "it seemed like a natural stopping point", and "it was not in the original request" are not blockers. The last one is worth naming directly: work that surfaced during the change and belongs to it is part of the change, not a follow-up.

## recording-a-scope-change

When work genuinely cannot land, record it as a scope change rather than as a remark. The record names what was dropped, why it was dropped, what specifically blocks it, and what it would take to finish. It goes where the next session will find it cold, which means the project's decision record or ideas notes, not only the conversation. The user is told in the same turn, in one line, as a change to what they are getting rather than as a footnote.

A scope change that exists only in a final message is not recorded. The session ends and the conversation is not the system of record.

## the-cost-record

Every scope change carries what it cost to get to that point, because that is the number that makes the next estimate better. Record the estimate that was made, the actual that was measured, and the variance between them.

This matters because the two are not close and not correlated in the way people assume. Prompt length does not predict cost. Measured on this machine, six prompts totalling an estimated 312 tokens of text produced 39.8M tokens of recorded traffic in one session, and a 961 token briefing handed to a dispatched agent produced 2.7M tokens of real traffic, a ratio of 2788 to 1. Those figures were measured on 2026-09-18 by code that counted each API turn once per content block, which overstated real transcripts about 2.5 to 2.7 times (corrected 2026-09-23); the true ratios are still in the thousands, so the conclusion stands. Cache reads dominate every total and do not scale with how long the instruction was.

So the useful estimate is not a token count derived from text. It is the count of dispatches, the tools a step will call, and how long each will run. A scope change records the estimate in those terms, the actual traffic that resulted, and the gap, so that the next decision to cut scope is made against a measured number rather than an intuition. `scripts/session-ledger.py` produces the actual side of that record for any session.

## relationship-to-other-rules

`find-fix-document` governs defects the work trips over, and requires the same three steps for a bug. This rule governs work the agent itself decided to drop, which is a different failure: the work was understood and was not a bug.

`open-decision-elicitation` governs choices only the user can resolve, and requires asking rather than defaulting. This rule covers what happens after that ask, and applies to everything that is not such a choice. Turning reachable work into an open decision to avoid doing it is the thing both rules forbid.
