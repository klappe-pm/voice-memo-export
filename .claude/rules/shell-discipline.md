# shell-discipline

## binding

One command per Bash call. Real work goes into committed scripts. Read and write files through the Read, Edit, and Write tools, not shell. The prose guard instruments only Write, Edit, and NotebookEdit; a write made through Bash, a heredoc, or an interpreter invocation never passes through it. The attribution guard runs on every tool call, Bash included, but checks attribution only. Keeping file changes on the editor tools is what keeps a change both guarded and reviewable. See `enforcement` below for what a hook actually checks in this rule.

## one-command-per-call

No `&&`, `;`, or `|` chains except `| head` or `| tail` when output would otherwise flood context. A compound call hides its individual steps behind one line in the transcript, which is harder for a reviewer to check than the same steps run and read one at a time.

## paths

Every command binds its own directory with an absolute path and the tool's directory flag; `command-cwd-scoping` is the rule and is not restated here.

## file-reads

Read files with the Read tool. Never `cat`, `sed -n`, or any shell substitution that reads a file into the call.

## file-writes

Change file content with Edit or Write. Never `sed -i`, `printf >>`, or a shell heredoc. Edit and Write run the repository's own guards and do not prompt for in-project paths. See `no-em-dash` and `no-hardwrapped-writing`: those guards see only Write and Edit, not shell output.

## loops-and-logic

Loops and multi-step logic go into a committed script under the tool's own directory or `scripts/`, with a test, run as one command. An inline `for ... do ... done` has no test and no committed source of its own, and its logic disappears from the record the moment the call scrolls past.

## python

Python runs only as a repository generator (`python3 <tool>/build-*.py`), a test runner (`python3 -m pytest ...`), or a one-off analysis whose output is discarded. A `python3 -` heredoc that writes into the tree is a generator without a contract, a test, or a committed source, and is not done here.

## pre-commit

Never run `pre-commit run --all-files` in this repository; its whitespace fixers rewrite evidence files. Run `pre-commit run --files` on only the text files a change actually rewrote. Bypassing this restriction requires explicit approval per `guard-bypass-approval`.

## enforcement

No hook enforces any clause in this rule today. The prose guard (`no-em-dash`, `no-hardwrapped-writing`) runs on every Write, Edit, and NotebookEdit call and sees only the content passed to those tools. The attribution guard (`no-agent-attribution`) is registered in `hooks/hooks.json` with no matcher, so it also inspects Bash commands and GitHub calls. Both enforce their own rules, not this one. Nothing here blocks a Bash file read, a heredoc, or a `sed -i` call before it runs. Every clause above is advisory: a convention a session is expected to follow, checked by review rather than by a gate.
