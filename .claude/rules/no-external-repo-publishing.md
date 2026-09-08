# no-external-repo-publishing

Never publish anything to a repository the user does not own. No pull requests, no pushes, no branches, no forks, no issues, no comments, no reviews, no releases. This holds for every repository whose owner is not the user, including one the user has cloned, contributes to, or has an open PR against.

The rule is absolute and standing. It is not satisfied by the work being finished, tested, reviewed, or obviously useful, and not by the task appearing to call for it.

## the-one-exception

The user asks for it explicitly, in that moment, naming the action. "Open a PR for this" authorizes that PR and nothing after it.

An approval is spent when it is used. It does not extend to the next PR, to a follow-up PR, to a documentation PR alongside the code PR, to reopening a closed one, or to pushing again after a rebase. Each outward-facing action needs its own yes, asked immediately before doing it. A long session makes this worse rather than better: the further an approval recedes into the transcript, the more likely it is being misremembered as broader than it was.

Silence is not approval. Neither is the user answering a different question, approving the work itself, or saying the change looks good.

## what-is-still-allowed

Everything local. Commit freely on a local branch, run the tests, write the files, keep the history clean. Local work is how the deliverable is preserved while the publishing decision stays with the user.

Reading a remote is fine: `git fetch`, `gh pr view`, `gh issue list`, cloning a public repo to read its source. The line is between reading and writing, not between local and remote.

Pushing to the user's own repositories follows the ordinary rules for outward-facing actions and is not covered here.

## when-the-work-looks-ready-to-ship

Say so and stop. Name the branch, the commit count, the test result, and what a PR would contain, then let the user decide. Offering is fine; acting is not.

If a fork or branch was already created on an external account, say that too, and offer to delete it. Do not quietly leave it there.

## why

Publishing to someone else's project acts in the user's name, in public, in a place they cannot fully retract. A PR notifies maintainers, enters their queue, and carries the user's identity and judgment. That is the user's call every single time, and the cost of asking once more is nothing against the cost of an unwanted PR on a stranger's repository.

This rule exists because it was violated: one approved PR was treated as standing permission, and two more were opened without asking.
