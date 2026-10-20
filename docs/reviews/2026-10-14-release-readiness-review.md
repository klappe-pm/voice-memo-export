---
domain: voice-memo-export
category: review
sub-category: release-readiness
topics:
  - ci
  - packaging
  - voice-memos
types:
  - review
date-created: 2026-10-14
date-revised: 2026-10-20
status: REVIEW
aliases: []
tags: []
models:
  - claude-opus-5-5
  - claude-sonnet-5-5
providers:
  - Anthropic
session-link: https://claude.ai/code/session_01Az7XTvkfwEd482CHWnDd6R
---

# 2026-10-14-release-readiness-review

This review records what stands between `vmea` on `main` and a release, with the command and output behind each finding. It is the baseline for increment 1 of the [voice to repository architecture](../design/voice-to-repo-architecture.md) and for the decisions in the [pipeline decision record](../adr/2026-10-14-voice-memo-to-repository-pipeline.md). Every command below was run on `main` at `ea83e5e` in a fresh virtual environment with `pip install -e ".[dev]"`.

## verdict

Not releasable. The command line tool does not import on Python 3.11, the lowest version the package claims to support, and the repository's own CI is red on lint and types. The tests that exist pass, but they cover a third of the code and almost none of the command line. Increment 1 of the delivery plan fixes everything in the blockers section before any new feature work.

## blockers

### the-cli-does-not-import-on-python-3-11

`src/vmea/cli.py:557` puts a backslash escape inside an f-string expression, which Python accepts only from 3.12. `pyproject.toml` declares `requires-python = ">=3.11"` and the CI matrix runs 3.11, so every 3.11 user gets a syntax error on the first `vmea` command.

```bash
python3.11 -c "import ast; ast.parse(open('src/vmea/cli.py').read())"
```

```text
SyntaxError: f-string expression part cannot include a backslash
```

### ci-is-red-on-lint-and-types

The CI workflow runs ruff and mypy before the tests, so the test step never gates a pull request.

```bash
ruff check src/vmea tests
```

```text
Found 29 errors.
[*] 20 fixable with `--fix` (3 unsafe fixes available with `--fix --unsafe-fixes`).
```

The errors are whitespace on blank lines, f-strings without placeholders, two unused variables in `setup_vmea_shortcut` and unused test arguments, plus the 3.11 syntax error above.

```bash
mypy src/vmea
```

```text
Found 3 errors in 2 files (checked 12 source files)
```

The three are an unused and too narrow `type: ignore` with a missing stub for `whisper` at `transcribe.py:46`, and `stat_result.st_birthtime` at `parser.py:351`, which exists on macOS but not on the Linux CI runner.

## major

### coverage-is-thin-where-it-matters

```bash
pytest --cov=vmea
```

```text
src/vmea/cli.py                  811    728    274      0     8%
src/vmea/transcribe.py            61     61     18      0     0%
TOTAL                           1746   1078    606     42    35%
92 passed
```

All 92 tests pass, but `cli.py`, which holds the export pipeline, the watcher and the daemon, is 8% covered and the Whisper path is not exercised at all.

### a-documented-command-does-not-exist

`setup_vmea_shortcut` in `cli.py` tells the user to run `vmea shortcut-setup`. No such command is registered; the commands are `init`, `export`, `watch`, `doctor`, `retry-failed`, `list`, `config` and the `ollama` and `daemon` groups.

### the-daemon-uses-a-deprecated-launchctl-call

`cli.py:1482` runs `launchctl load`, which current macOS treats as legacy, and the plist template interpolates paths without XML escaping, so a home directory containing `&` or `<` writes an invalid plist. The fix is `launchctl bootstrap gui/<uid>` with escaped values.

## minor

- The README and `pyproject.toml` still point at the old repository name, `Apple-Voice-Memo-Export-to-Markdown` (`README.md:41`, `pyproject.toml:58`).
- The README has an odd number of code fence markers (21), so the installation block never closes and the rest of the page renders as code.
- Files under `docs/` use uppercase names such as `GETTING_STARTED.md`, against the repository naming rule.

## not-yet-reviewed

A correctness pass over the export pipeline (`export_memo`, `cleanup.py`, `writer.py`, `state.py`) was started and did not report before this review was written. Its findings, if any, go into a follow-up revision of this page. The parsing layer was later extracted into a separate package and reviewed adversarially there, and the hardening it needed (bounded MP4 walking, safe plist search, no symlink following, terminal safe output) applies equally to `discovery.py` and `parser.py` here.
