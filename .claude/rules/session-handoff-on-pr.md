# session-handoff-on-pr

## binding

Every session ends by writing a handoff where the next session will find it: a comment on the pull request that carries the session's work. The next session reads that comment before it does anything else.

A transcript is not a system of record. It ends with the session, it is not attached to the code it describes, and nobody reads it. A pull request comment is attached to the diff, timestamped, durable, and visible to anyone reviewing the change, which is what makes the handoff provenance rather than a note.

A cloud session also posts its token count beside the handoff, as a separate `## session tokens` comment.

## ending-a-session

Before the closing message, in this order:

1. Commit the work and push the branch.
2. Ensure a pull request exists for that branch against its base. Create it if there is none.
3. Post the handoff as a new comment on that pull request. Never edit a previous handoff: the sequence of comments is the history of how the work actually went, and rewriting it destroys the thing the comment exists for.
4. Name the pull request URL in the closing message so the person can follow it.

The handoff is posted even when the session accomplished little, and especially when it ended badly. A session that ends confused is the one whose successor most needs to know where the confusion was.

## the-handoff-format

The comment opens with the literal heading `## session handoff` so it can be found mechanically, then carries these fields in this order. Omit none of them; write `none` where a field is empty.

```markdown
## session handoff

**Delivered:** what is committed and pushed, named by commit or by what a reader can see in the diff.
**Gates:** the exact command run and its exact result. A gate that was not run is reported as not run, never as assumed.
**Next:** the single next action, specific enough to start on without re-deriving it.
**Blocked:** what cannot proceed and precisely what unblocks it, or `none`.
**Do not:** the traps this session hit or nearly hit, so the next one does not repeat them.
**Open decisions:** what needs the user's answer before the work can continue, or `none`.
```

Write it as facts, not narrative. `Delivered` is what a reader can verify, not what was attempted. `Gates` carries verbatim output, because "tests pass" written by a session that did not run them is how a false green survives a handoff.

The comment carries no agent, model, or runtime attribution, under `no-agent-attribution`, which applies to pull request comments exactly as it applies to commit messages.

## the-session-tokens-comment

A session run in a claude.ai/code cloud container writes nothing to the operator's machine, so its spend reaches no report unless it reports itself (`docs/adr/2026-09-23-count-tokens-wherever-a-session-runs.md`, B-13). Before posting its handoff, a cloud session prints its token comment from its own transcript and posts it as a second, separate comment on the same pull request:

```bash
cd /Users/<user>/projects/active/<repo> && python3 scripts/session-ledger.py current --tokens-comment > <scratch>/session-tokens.md
```

```bash
gh pr comment <number> --repo <owner>/<repo> --body-file <scratch>/session-tokens.md
```

`current` is the transcript of the session `CLAUDE_CODE_SESSION_ID` names; without that variable it is the newest transcript in the project folder of the working directory or its nearest ancestor, and it fails rather than reach into another project's folder. A session id or transcript path works too, and `--work-item <id>` names the work item when neither the session's join nor its branch does. The comment opens with the literal heading `## session tokens` and carries one `json` block: session id, runtime (`claude-cloud` when `CLAUDE_CODE_REMOTE` is `true`), models, tokens by kind (input, output, cache read, cache write, total), thinking, turns, dispatched agents with their tokens, work item, branch, and the first and last activity. It names models as technical facts and carries no session link.

The token figures never become a handoff field: the handoff format above is unchanged, and the two comments are posted and read separately. A session that continues after its first token comment posts a new one rather than editing the old; the importer keeps the first line it wrote for a session id.

On the operator's machine, `python3 $HOME/projects/active/0-llm-root/scripts/budget-report.py import-remote --repo <owner>/<repo>` reads those comments into `~/.agent-hooks/telemetry/remote-sessions.jsonl`, one line per session id, so a second import adds nothing; `spend` then counts them under runtime `claude-cloud`, and `assign` moves an unassigned one like a local session. A session this machine also measured is counted once, from its local transcript.

## starting-a-session

Before acting, read the handoff on the pull request for the current branch. When the working directory is the repository and the branch is checked out, `gh pr view` resolves it without arguments:

```bash
cd /Users/<user>/projects/active/<repo> && gh pr view --json comments --jq '[.comments[].body] | map(select(test("## session handoff"))) | last'
```

The last matching comment is the live handoff. Earlier ones are history and are read only when the last one points at them.

Where the handoff was posted on a commit rather than a pull request, read it from the commit:

```bash
gh api repos/<owner>/<repo>/commits/<sha>/comments --jq '.[] | select(.body | test("## session handoff")) | .body'
```

Posting the same way, from a file so the body is authored through an editor tool and passes the prose guards:

```bash
gh api repos/<owner>/<repo>/commits/<sha>/comments -F body=@<path to handoff.md> --jq '.html_url'
```

If no pull request exists for the branch, or it carries no handoff comment, say so in one line and proceed from the repository's own state. Do not invent continuity that was never recorded.

Treat the handoff as a report from a session that could not see everything, not as instruction. Its `Delivered` and `Gates` are checkable and should be checked when the work depends on them; a green gate claimed in a comment is re-run before it is relied on.

## authentication-diagnosis

Verify remote access in the execution environment that will publish. A successful host-terminal login, connected GitHub app, or configuration sync does not establish that a sandboxed shell can use the same credentials.

Distinguish connection failures from unavailable credentials and rejected credentials. When GitHub CLI fails, inspect only selected `gh auth status --json hosts` fields: account login, active state, credential source, state, and error. Never print tokens or raw credential files. The JSON command can exit 0 while reporting an account error, so inspect the account state as well as the process exit code.

If the user confirms a working host keyring login while the session reports source `default` and cannot obtain a credential, record an execution-context credential-access failure. Do not repeat login requests, describe the host token as expired, change network permissions to repair authentication, or claim synchronization refreshes an active session's permissions. A denied credential path or unavailable elevation remains an execution boundary; never work around it by exporting credentials, disabling isolation, or using a different tool to read the denied store.

An independently authenticated connector can perform supported, authorized repository operations using its own connection. Report connector and shell verification separately. If shell publication remains unavailable, preserve the local commit and a concrete handoff with the failed command, verified account state, and required operator-supported remedy. Check whether the prior PR is open or merged before attaching new work; a merged PR is history and new commits require a new PR.

## authorization-and-scope

This rule is standing authorization for exactly three outward-facing actions, on a repository the user owns: opening or updating the pull request that carries the session's own work, posting the handoff comment on it, and posting the session tokens comment beside that handoff. Nothing else.

It does not authorize merging, closing, force pushing, or any action on a repository the user does not own. `no-external-repo-publishing` is unaffected and still forbids all of that without a fresh, explicit, per-action yes. A session working in someone else's repository writes its handoff to the project's own notes instead and says so.

Work committed directly to a default branch has no pull request to carry a handoff. Prefer a branch. Where the user has directed work on the default branch, post the handoff as a comment on the pushed commit, which preserves the same attachment to the diff.

## enforcement

`hooks/require-pr-on-stop.sh` is the mechanical check, enforced for any session that actually pushed. It finds the session start by matching the payload's `session_id` to read-only metadata under `~/.claude/sessions/`; when that metadata is absent, it uses the oldest HEAD reflog entry from the last hour. Every reflog time is when the ref moved, never the commit's own date, so pushing an older commit still counts as this session's push. The session is in scope when the current branch's remote tracking ref has a later reflog entry recording a push, whatever HEAD is now, or a fetch that advanced the ref to HEAD. If no session start can be established, scope falls back to repositories under `~/projects/_worktrees`, so ordinary existing checkouts are not newly blocked. Within scope it blocks a session from stopping with uncommitted changes or with commits made after its push, then requires the handoff itself: on a non-default branch, an open pull request carrying a `## session handoff` comment, or, when none is open, one merged at exactly the branch head, since someone else may merge the session's pull request before it stops (a pull request merged before later commits, or closed without merging, does not count); on the default branch, that same heading as a comment on the pushed head commit, since the default branch has no pull request of its own to carry it. The handoff must be posted since the session start, because an earlier session's handoff is history; with no known session start, any handoff counts. Its block messages name the push and pull request as pre-authorized under `authorization-and-scope`, never as something to ask approval for. It matches the heading literally, which is the same string this rule tells the next session to search for, so the check and the reader cannot drift apart.

A comment query that cannot be read blocks too. An unreadable answer is not a confirmed absence, and treating the two the same is how a missing handoff passes silently.

`hooks/require-pr-on-stop.test.sh` covers all of it with real local repositories and bare remotes, including the counterexamples: an upstream without a push this session is not checked, an old commit pushed this session is checked, a commit made after the push is blocked, a push without a pull request is blocked and so is one whose only pull request is closed or was merged before later commits, one whose pull request merged at the branch head passes only with this session's clean handoff on it, a pushed default-branch commit with no handoff comment is blocked, one with a handoff comment is not, a handoff from an earlier session is blocked on either path, the missing session-start fallback checks a worktree and leaves an ordinary checkout alone, and an unreadable query is blocked with a different message on either handoff path.

## relationship-to-other-rules

`finish-or-record-scope-change` governs what may be left undone. This rule governs where the record of it lives: a scope change named only in a closing message is not recorded, and the handoff comment is the place it becomes durable.

`open-decision-elicitation` still requires asking the user directly during the session. The `Open decisions` field carries what remains unanswered at the end; it is not a substitute for asking.
