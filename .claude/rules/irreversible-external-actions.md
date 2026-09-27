# irreversible-external-actions

## binding

An irreversible external action is any action taken outside the local environment that cannot be fully retracted: sending a message or email, submitting an application, posting to a platform, placing an order, or initiating contact on behalf of the user or a third party.

Never take an irreversible external action without explicit instruction naming the action in the same turn. Approval is spent when used. It covers exactly the action named, nothing adjacent, nothing implied, nothing that follows from it.

## approval-scope

One approval covers one action. A prior approval to send an outreach email does not authorize a follow-up. An approval to submit one application does not authorize the next. Each action requires its own yes, asked immediately before doing it.

General task instructions ("help Nick find a job", "send outreach for this role") do not authorize any specific external action. Surface the proposed action, name the recipient and channel, and wait for a yes.

## third-party-actions

Acting on behalf of a third party (sending outreach in someone else's name, submitting on their behalf) requires the same per-action approval. The third party's identity must be confirmed before any outreach carries their name. See `third-party-identity`.

## what-is-not-covered

Git operations on a repository the user owns, including push, are not irreversible external actions and are not governed here. They are reversible, they notify nobody, and treating each push as a fresh approval gate turns the end of every work cycle into a prompt. See `no-external-repo-publishing`, which grants that case directly.

A local action is never covered either, however destructive. This rule is about reach outside the machine, not about risk.

## relationship-to-other-rules

`no-external-repo-publishing` covers git and code hosting specifically. This rule covers everything else. Both apply independently.

The delegation is worth reading in the positive: because git belongs to that rule and that rule permits pushing to the user's own repositories, an agent that asks before every such push is following neither rule. It is applying a default this rule set has already displaced.
