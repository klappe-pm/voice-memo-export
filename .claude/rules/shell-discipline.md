# shell-discipline

One command per Bash call. Real work goes into committed scripts. Read and write files through the Read, Edit, and Write tools, not shell. These rules exist because each compound call, heredoc, and interpreter invocation is a permission-classifier candidate; the allowlist in `.claude/settings.json` covers only the narrow read-only tools this repo needs (`pdftotext`, `pdfinfo`, `ruff check`, `ruff format --check`, `pytest`, `shasum`, `md5`).

## one-command-per-call

No `&&`, `;`, or `|` chains except `| head` or `| tail` when output would otherwise flood context. A permission rule approves a call only when every segment matches a rule; one unmatched segment sends the whole call to the classifier.

## paths

Use absolute paths or worktree-relative paths. Never `cd X && ...`. Prefer the tool's own directory flag: `git -C <path>`, `python3 <absolute-or-repo-relative script>`.

## file-reads

Read files with the Read tool. Never `cat`, `sed -n`, or any shell substitution that reads a file into the call.

## file-writes

Change file content with Edit or Write. Never `sed -i`, `printf >>`, or a shell heredoc. Edit and Write run the repository's own guards and do not prompt for in-project paths. See `no-em-dash` and `no-hardwrapped-writing`: those guards see only Write and Edit, not shell output.

## loops-and-logic

Loops and multi-step logic go into a committed script under the tool's own directory or `scripts/`, with a test, run as one command. An inline `for ... do ... done` cannot match any permission rule.

## python

Python runs only as a repository generator (`python3 <tool>/build-*.py`), a test runner (`python3 -m pytest ...`), or a one-off analysis whose output is discarded. A `python3 -` heredoc that writes into the tree is a generator without a contract and is not done here. Interpreters cannot be allow-listed: an allow rule for `python3` would grant arbitrary code execution, so every Python call is judged by the classifier.

## pre-commit

Never run `pre-commit run --all-files` in this repository; its whitespace fixers rewrite evidence files. Run `pre-commit run --files` on only the text files a change actually rewrote. Bypassing this restriction requires explicit approval per `guard-bypass-approval`.

## context

The 2026-09-02 analysis in `docs/backlog/2026-09-02-permission-prompts-root-cause-and-remedy.md` measured 2,056 Bash calls across recent sessions: 81 percent compound, 321 heredocs. Each is a prompt candidate. Keeping calls simple and moving real work into committed generators is what makes the prompts stop.
