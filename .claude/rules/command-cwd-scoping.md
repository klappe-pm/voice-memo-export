# command-cwd-scoping

## binding

Every terminal command an agent hands to the user must carry its own working directory. A command printed in a turn, a doc, a PR body, or a runbook is read and run somewhere else: a fresh shell, a new Claude Code or Codex session, a different tab, or a different machine. That reader does not inherit this session's current directory and cannot be told to "run this from the repo root" reliably. An unscoped command is therefore a defect, not a shorthand.

## the-requirement

Bind the directory in the command itself, using absolute paths (`/Users/...` or `$HOME/...`), never a bare relative path and never prose instructions about where to stand.

Prefer the tool's own directory flag when it has one, because it scopes without changing the shell's state:

```bash
git -C /Users/you/Projects/example status
make -C /Users/you/Projects/example test
npm --prefix /Users/you/Projects/example run build
pytest /Users/you/Projects/example/tests
```

When the tool has no such flag, lead the block with an explicit `cd` to an absolute path:

```bash
cd /Users/you/Projects/example && ./scripts/validate.sh
```

## copy-paste-blocks-are-self-sufficient

Users copy one fenced block at a time, so each block must stand alone. A block that depends on a `cd` from an earlier block is broken the moment someone copies only the second block. Either scope every block independently, or emit one block that opens with the `cd` and contains every command that follows it.

Anchor the path to something durable. Name the real project path (`/Users/<user>/Projects/<slug>`), not a scratch, staging, or worktree path that will not exist for the reader. When the command must run in a linked worktree, print that worktree's full absolute path, since the reader has no way to guess it.

## scope

This applies to every command an agent emits for a human or another session to run, on every surface: chat output, plans, decision records, ideas notes, PR and issue bodies, and generated runbooks.

It also applies to commands the agent runs through its own tools, with one adjustment: prefer the directory flag (`git -C`, `make -C`, `--prefix`) over `cd`. Changing directory to reach a target can defeat path and scope guards, which `guard-bypass-approval` forbids, and a `cd` inside a compound command is what trips several of the repo guards in the first place.

The single exception is a command whose meaning is deliberately relative to wherever the user already is, such as a one-line diagnostic the user is being asked to run in an unknown directory. State that intent explicitly in the surrounding line; do not leave it implied.
