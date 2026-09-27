# output-format-contract

## binding

When a file, prior session, or explicit instruction defines an output format for a task, that format is the contract. Do not re-derive, simplify, or improve it without instruction.

## what-counts-as-a-contract

A format is contracted when any of these are true:

- The owning file specifies field order, labels, or structure (e.g. a discovery response template, a briefing schema, a status report shape).
- A prior explicit instruction in the same project named the format.
- The user has corrected a format deviation in a prior session and the correction is recorded in the project's memory or CLAUDE.md.

## applying-the-contract

Follow the contract exactly: field order, labels, punctuation rules, presence or absence of decoration (bold, headers), and rewrite language. Do not add fields the contract omits. Do not omit fields the contract requires. Do not change decoration unless instructed.

When a contract is ambiguous on a specific case, ask once and record the answer before proceeding.

## contract-vs-style-rules

Global style rules (`no-em-dash`, `no-hardwrapped-writing`) apply inside a contracted format. A format contract does not override global rules; it narrows the remaining degrees of freedom.
