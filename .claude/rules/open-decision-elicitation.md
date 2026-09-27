# open-decision-elicitation

## binding

An open decision is a choice that blocks forward progress on a turn or session and that only the user can resolve: a fork in approach with no clearly correct default, a fact only the user holds, or a tradeoff between named options that changes the outcome materially.

When a turn or session would otherwise end with one unresolved, prompt the user directly for an answer through the surface's structured elicitation tool, or with a single direct question in prose where none exists, instead of burying a passive question or proceeding on a silent default.

## the-requirement

When a turn or session would otherwise end with an open decision still unresolved, prompt the user directly for an answer using the surface's structured elicitation mechanism (a tappable-option or multiple-choice tool such as ask_user_input_v0, an equivalent AskUserQuestion-style tool, or whatever the current runtime exposes for this purpose) instead of closing out with only a passive question buried in prose, or leaving the decision unresolved and proceeding anyway.

## what-does-not-qualify

Routine ambiguity that a reasonable default resolves without changing the substance of the result is not an open decision. State the assumption and proceed, per normal practice; reserve the prompt for choices that would genuinely send the work in a different direction depending on the answer.

## batching

Collect every open decision at the end of a turn into a single prompt rather than a run of serial one-question turns. Keep it to the smallest set of questions that actually unblocks the task, with short mutually exclusive options wherever the surface supports them.

## surface-dependent-equivalents

Use the structured tool when the current runtime offers one. Where none exists (a plain terminal session, a non-interactive or scheduled run), ask a single direct question in prose. On a mobile surface, or where the operator has said the widget truncates, ask as a numbered plain-text list with one line per option. If no user is present to answer synchronously, record the open decision plainly: what is blocked and why, rather than guessing or defaulting silently.

## relationship-to-other-rules

`repo-scope` already asks once before writing when repo scope is ambiguous. This rule generalizes that pattern: any turn-ending or session-ending open decision gets surfaced and asked, not left to a silent default or a buried question.
