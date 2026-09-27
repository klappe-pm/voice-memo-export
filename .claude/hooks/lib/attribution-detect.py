#!/usr/bin/env python3
"""Shared detection and stripping for agent authorship attribution.

Backs rules/no-agent-attribution.md. Runtime system prompts routinely append
authorship credit to commit messages, pull request bodies, and file footers:
a co-author trailer naming a model, a "generated with" line, a session
permalink, a robot emoji byline. The user's standing rule is that authored
output carries no agent attribution, so this module is the single detection
implementation behind both enforcement points:

  * the PreToolUse guard hooks/no-attribution-guard.sh, which denies a write,
    an authoring shell command, or a GitHub MCP call whose text carries
    attribution before it lands, and
  * the git commit-msg backstop scripts/git-hooks/strip-commit-attribution.sh,
    which silently strips the offending lines out of a commit message written
    directly with plain git (bypassing the runtime) at commit time.

Keeping one detector means the two paths can never drift.

Public functions:
  detect(text) -> str            label of the first attribution form found,
                                 or "" when the text is clean
  strip(text) -> str             the text with every attribution line removed
                                 and the trailing separator it left behind
                                 cleaned up
  detect_in_payload(payload) -> str
                                 the hook path: reads a PreToolUse payload and
                                 scans only the fields that carry authored
                                 text for the tool in question

CLI: attribution-detect.py detect reads text on stdin and prints the label
(one line) when attribution is found, prints nothing when clean, always exits
0. attribution-detect.py detect-payload reads the PreToolUse JSON payload on
stdin instead of bare text. attribution-detect.py strip reads text on stdin
and writes the cleaned text on stdout. Input is read as bytes, so text in any
encoding is judged, and strip writes untouched bytes back unchanged. A
nonzero exit signals a usage error or a crash, never a detection result, so
callers distinguish "clean" from "broke" by exit status and treat "broke" as
a failed gate.

Determinism: pure Python stdlib, no network, no model calls.

Self-avoidance: every pattern below is written so that this source file does
not itself match it (a regex metacharacter always sits where the literal text
would have to continue). That keeps the guard from denying edits to its own
detector.
"""

import json
import os
import re
import shlex
import sys

# Names that identify a coding agent or its vendor in an attribution line.
# Word boundaries on both sides are load bearing: without them "example.com"
# contains an agent name and every human co-author trailer is a false deny.
_AGENT = (
    r"\b(?:Claude|Anthropic|Codex|OpenAI|ChatGPT|GPT-[0-9]|Copilot|Cursor"
    r"|Devin|Gemini|Aider|Windsurf|AI assistant|AI agent|LLM)\b"
)

# A trailer normally opens a line, but inside a shell command it opens a
# quoted argument instead (git commit -m "Co-Authored-By: ..."), so a quote
# counts as a line start for detection. Stripping stays line oriented.
_LINE_START = r"(?:^|[\"'`])[ \t>*_-]*"

# One "label|pattern" pair per attribution form. Add a new form as its own
# entry; do not fold forms into a shared monolith regex. All matching is
# case-insensitive and line-oriented: a match marks the whole physical line
# for removal, which is the shape attribution always takes.
# A repository content path (an issue, a pull request, a release, a
# documentation page, and the other paths a citation legitimately links to)
# is not a product landing page, even under a vendor's own org on GitHub.
# 2026-09-21, F-22: the unnarrowed agent-product-link pattern denied a
# descriptive citation of a GitHub issue in the vendor's own repository
# (docs/ideas/attribution-detector-issue-link-false-positive.md), because its
# URL check only looked for the vendor's name anywhere in the link, not at
# whether the link actually pointed at repository content.
_REPO_CONTENT_PATH = (
    r"(?:issues|pull|pulls|releases|blob|tree|wiki|discussions|commit|compare|docs)/"
)
_GITHUB_REPO_CONTENT_URL = (
    r"github\.com/[^/)\s]+/[^/)\s]+/" + _REPO_CONTENT_PATH
)

_PATTERNS = (
    ("co-author-trailer", _LINE_START + r"Co[- ]?Authored[- ]?By:[^\n]*" + _AGENT),
    ("assisted-by-trailer", _LINE_START + r"(?:Assisted|Generated)[- ]?By:[^\n]*" + _AGENT),
    ("generated-with", r"(?:Generated|Created|Authored|Written|Built)\s+(?:with|by)\b.{0,40}?" + _AGENT),
    ("agent-vendor-email", r"noreply@(?:anthropic|openai)\.com"),
    ("session-permalink", r"claude\.(?:ai|com)/(?:code|share|chat)/[A-Za-z0-9_-]+"),
    ("session-trailer", _LINE_START + r"(?:Claude|Codex|Agent)[- ]Session:"),
    (
        "agent-product-link",
        r"\[[^]]*(?:Claude Code|Claude|Codex|Copilot)[^]]*\]"
        r"\(https?://(?!" + _GITHUB_REPO_CONTENT_URL + r")"
        r"[^)\s]*(?:anthropic|claude|openai|github\.com/features/copilot)[^)\s]*\)",
    ),
    ("robot-byline", "\U0001F916"),
)

_COMPILED = tuple(
    (label, re.compile(pattern, re.IGNORECASE | re.MULTILINE))
    for label, pattern in _PATTERNS
)

# The one place a session link is metadata rather than credit: the
# `session-link:` frontmatter key that rules/docs-provenance-frontmatter.md
# requires on agent-written docs files (the provenance-exception section of
# rules/no-agent-attribution.md). The exception covers the frontmatter of a
# Markdown file under a docs/ directory and nothing else, so it is decided on
# the payload path, where the target file is known: detect_in_payload exempts
# the session-permalink form on such a line of a Write or Edit to such a file.
# Bare text (a commit message, a pull request body, a handoff comment) is
# never docs frontmatter, so detect() exempts nothing unless a caller that
# knows better asks it to. strip() never honours it: it runs on commit
# messages, which never legitimately carry the key.
#
# 2026-09-23, review cluster F2: detect() used to exempt every such line by
# default, so the commit-msg backstop (which gates strip on detect) let a
# `session-link:` permalink through a plain git commit, and the guard let one
# through a gh pr body, an MCP message, and a handoff comment.
_PROVENANCE_LINE = re.compile(r"^[ \t]*session-link:", re.IGNORECASE)
_PROVENANCE_EXEMPT = frozenset({"session-permalink"})
_SESSION_PERMALINK = next(pattern for label, pattern in _COMPILED if label == "session-permalink")
_DOCS_MARKDOWN_PATH = re.compile(r"(?:^|/)docs/(?:[^/]+/)*[^/]+\.md$", re.IGNORECASE)


def _without_provenance_lines(text):
    return "\n".join(
        line for line in text.split("\n") if not _PROVENANCE_LINE.match(line)
    )


def _frontmatter_end(lines):
    """Index of the closing --- of a leading frontmatter block, else -1."""
    if not lines or lines[0].strip() != "---":
        return -1
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index
    return -1


def _without_frontmatter_provenance(before, text, after=""):
    """text with permitted session permalinks in docs frontmatter removed.

    before and after are the file text around text once the write lands (both
    "" for a whole-file Write), so an Edit fragment is judged by where it sits
    in its file. A line is exempt only when it opens with the key and lies
    strictly between the file's leading --- fences; other text is kept.
    """
    document = (before + text + after).split("\n")
    end = _frontmatter_end(document)
    first = before.count("\n")
    kept = []
    for offset, line in enumerate(text.split("\n")):
        index = first + offset
        # The whole physical line decides, since text's first line may
        # continue the tail of before; only text's own part is changed.
        if 0 < index < end and _PROVENANCE_LINE.match(document[index]):
            kept.append(_SESSION_PERMALINK.sub("", line))
        else:
            kept.append(line)
    return "\n".join(kept)


def _docs_markdown_target(tool_input):
    path = tool_input.get("file_path")
    return isinstance(path, str) and bool(_DOCS_MARKDOWN_PATH.search(path))


def _read_edit_file(file_path):
    if not isinstance(file_path, str):
        return None
    try:
        with open(file_path, "rb") as handle:
            existing = handle.read(_BODY_FILE_LIMIT + 1)
    except (OSError, ValueError):
        return None
    if len(existing) > _BODY_FILE_LIMIT:
        return None
    return existing.decode("utf-8", errors="replace")


def _edit_context(tool_input, existing):
    """Offsets for every replacement location in existing, else None."""
    old_string = tool_input.get("old_string")
    if not isinstance(old_string, str) or not old_string or existing is None:
        return None
    offsets = []
    start = 0
    while (index := existing.find(old_string, start)) >= 0:
        offsets.append(index)
        if not tool_input.get("replace_all"):
            break
        start = index + len(old_string)
    return offsets or None


def _detect_edit_at_locations(edit, existing, offsets):
    old_length = len(edit["old_string"])
    for index in offsets:
        subject = _without_frontmatter_provenance(
            existing[:index], edit["new_string"], existing[index + old_length:]
        )
        label = detect(subject)
        if label:
            return label
    return ""


def _detect_authored_document(document, authored):
    """Detect new attribution in the final document, with docs provenance exempted."""
    lines = document.split("\n")
    end = _frontmatter_end(lines)
    exempt = bytearray(len(document))
    offset = 0
    for index, line in enumerate(lines):
        if 0 < index < end and _PROVENANCE_LINE.match(line):
            for match in _SESSION_PERMALINK.finditer(line):
                exempt[offset + match.start():offset + match.end()] = b"\1" * len(match.group())
        offset += len(line) + 1
    for label, pattern in _COMPILED:
        for match in pattern.finditer(document):
            start, stop = match.span()
            if b"\1" not in authored[start:stop]:
                continue
            if label == "session-permalink" and all(exempt[start:stop]):
                continue
            return label
    return ""


def _detect_write(tool_name, tool_input):
    """detect() for a file write, with the docs frontmatter exception applied."""
    text = "\n".join(_strings(tool_input, _WRITE_FIELDS))
    label = detect(text)
    if label not in _PROVENANCE_EXEMPT or not _docs_markdown_target(tool_input):
        return label
    if tool_name == "Write" and isinstance(tool_input.get("content"), str):
        return detect(_without_frontmatter_provenance("", tool_input["content"]))
    elif tool_name == "Edit" and isinstance(tool_input.get("new_string"), str):
        existing = _read_edit_file(tool_input.get("file_path"))
        offsets = _edit_context(tool_input, existing)
        if offsets is None:
            return label
        return _detect_edit_at_locations(tool_input, existing, offsets)
    elif tool_name == "MultiEdit" and isinstance(tool_input.get("edits"), list):
        existing = _read_edit_file(tool_input.get("file_path"))
        authored = bytearray(len(existing or ""))
        for edit in tool_input["edits"]:
            if not isinstance(edit, dict) or not isinstance(edit.get("new_string"), str):
                return label
            offsets = _edit_context(edit, existing)
            if offsets is None:
                return label
            old_length = len(edit["old_string"])
            replacement = edit["new_string"]
            parts = []
            flags = bytearray()
            start = 0
            for index in offsets:
                parts.extend((existing[start:index], replacement))
                flags.extend(authored[start:index])
                flags.extend(b"\1" * len(replacement))
                start = index + old_length
            parts.append(existing[start:])
            flags.extend(authored[start:])
            existing = "".join(parts)
            authored = flags
        return _detect_authored_document(existing, authored)
    else:
        return label


# Fields that carry newly authored text, by tool family.
_WRITE_FIELDS = ("content", "new_string", "new_source")
_MESSAGE_FIELDS = (
    "body",
    "commit_message",
    "message",
    "title",
    "description",
    "text",
    "content",
)

# Shell commands that publish authored text. A Bash payload is scanned only
# when the command is one of these, so an ordinary grep for an attribution
# string is not itself treated as a violation.
# Git global options may sit before the subcommand: `git -C <path> commit` is
# the spelling rules/command-cwd-scoping.md requires, and before WI-55 it hid
# every such commit from this check.
_GIT_GLOBAL_OPTIONS = (
    r"(?:\s+(?:-[Cc]\s+\S+|--(?:git-dir|work-tree|namespace)\s+\S+"
    r"|--?[A-Za-z][\w-]*(?:=\S*)?))*"
)
_AUTHORING_COMMAND = re.compile(
    r"\b(?:git" + _GIT_GLOBAL_OPTIONS + r"\s+(?:commit|tag|notes|merge|revert|cherry-pick|rebase)"
    r"|gh\s+(?:pr|issue|release|gist|api)"
    r"|glab\s+(?:mr|issue|release))\b"
)


# Tools whose input is local bookkeeping that is never published, so their
# message-shaped fields (a todo item's "content", for instance) are not judged.
# The guard runs on every tool (A-03), which is what makes this list needed.
_LOCAL_TOOLS = frozenset({"TodoWrite"})

# A body file larger than this is not read: the hook runs under a 3 second
# timeout, and a message body is never this large.
_BODY_FILE_LIMIT = 1024 * 1024

# Shell operators that separate one simple command from the next.
_SHELL_OPERATOR = re.compile(r"^[;&|()]+$")
_GIT_FILE_SUBCOMMANDS = frozenset({"commit", "tag", "notes", "merge"})
_GIT_OPTIONS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})
_GH_FILE_SUBCOMMANDS = frozenset({"pr", "issue", "release", "api"})
_GH_BODY_FILE_FLAGS = frozenset({"--body-file", "--notes-file"})
_GH_FIELD_FLAGS = frozenset({"-F", "--field"})


def _segments(command):
    """Split a shell command into simple commands, as token lists.

    Each operator run between commands is kept as a one-item list holding
    the operator token, so the caller can see a subshell open and close.
    Returns None when the command cannot be tokenized (unbalanced quotes),
    so the caller falls back to scanning the command text alone.
    """
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None
    segments, current = [], []
    for token in tokens:
        if _SHELL_OPERATOR.match(token):
            if current:
                segments.append(current)
            segments.append([token])
            current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def _expand(path, base):
    """A command-line path, expanded and made absolute against base."""
    path = os.path.expandvars(os.path.expanduser(path))
    if not os.path.isabs(path) and base:
        path = os.path.join(base, path)
    return path


def _git_body_files(args, cwd):
    """(path, kind) for each file a git authoring subcommand reads a message from.

    Git runs as if started in the directory its -C options name (several
    compound, a relative one against the one before), and resolves -F there.
    """
    index, base = 0, cwd
    while index < len(args) and args[index].startswith("-"):
        if args[index] == "-C" and index + 1 < len(args):
            base = _expand(args[index + 1], base)
        index += 2 if args[index] in _GIT_OPTIONS_WITH_VALUE else 1
    if index >= len(args) or args[index] not in _GIT_FILE_SUBCOMMANDS:
        return []
    paths, rest = [], args[index + 1:]
    for position, token in enumerate(rest):
        following = rest[position + 1] if position + 1 < len(rest) else ""
        if token in ("-F", "--file"):
            paths.append(following)
        elif token.startswith("--file="):
            paths.append(token[len("--file="):])
        elif token.startswith("-F") and len(token) > 2:
            paths.append(token[2:])
    return [(_expand(path, base), "text") for path in paths if path and path != "-"]


def _gh_body_files(args, cwd):
    """(path, kind) for each file a gh publishing subcommand reads a body from."""
    if not args or args[0] not in _GH_FILE_SUBCOMMANDS:
        return []
    subcommand, paths, rest = args[0], [], args[1:]
    for position, token in enumerate(rest):
        following = rest[position + 1] if position + 1 < len(rest) else ""
        flag, _, attached = token.partition("=")
        if token in _GH_BODY_FILE_FLAGS:
            paths.append((following, "text"))
        elif flag in _GH_BODY_FILE_FLAGS:
            paths.append((attached, "text"))
        elif subcommand == "api" and token == "--input":
            paths.append((following, "json"))
        elif subcommand == "api" and flag == "--input":
            paths.append((attached, "json"))
        elif token in _GH_FIELD_FLAGS or flag == "--field":
            value = following if token in _GH_FIELD_FLAGS else attached
            key, sep, source = value.partition("=")
            if sep and source.startswith("@") and key in _MESSAGE_FIELDS:
                paths.append((source[1:], "text"))
            elif not sep and token == "-F" and subcommand != "api":
                # gh pr, gh issue: -F is --body-file; gh release: --notes-file.
                paths.append((value, "text"))
    return [(_expand(path, cwd), kind) for path, kind in paths if path and path != "-"]


def _body_file_paths(command, cwd):
    """(absolute path, kind) for every file an authoring command names as a body."""
    segments = _segments(command)
    if not segments:
        return []
    paths, outer = [], []
    for tokens in segments:
        if _SHELL_OPERATOR.match(tokens[0]):
            # A subshell's cd ends with the subshell: ( pushes, ) restores.
            for char in tokens[0]:
                if char == "(":
                    outer.append(cwd)
                elif char == ")" and outer:
                    cwd = outer.pop()
            continue
        # A cd (or pushd) earlier in the command moves every later relative
        # path, the `cd <dir> && gh ...` form command-cwd-scoping allows.
        if tokens[0] in ("cd", "pushd") and len(tokens) > 1 and not tokens[1].startswith("-"):
            cwd = _expand(tokens[1], cwd)
            continue
        # Look through any wrapper in front of the publishing program: env,
        # op run --, and the credential launcher (credentials.py run or
        # llm-auth run, rules/secret-resolution.md), whose --cwd is the
        # directory the child runs in.
        base = cwd
        for index, token in enumerate(tokens):
            program = os.path.basename(token)
            if program in ("git", "gh"):
                args = tokens[index + 1:]
                finder = _git_body_files if program == "git" else _gh_body_files
                paths.extend(finder(args, base))
                break
            following = tokens[index + 1] if index + 1 < len(tokens) else ""
            if token == "--cwd" and following:
                base = _expand(following, base)
            elif token.startswith("--cwd="):
                base = _expand(token[len("--cwd="):], base)
    return paths


def _read_body_file(path, kind):
    """The file's text to scan, or "" when it cannot be read: unreadable is absent.

    A JSON request body (gh api --input) escapes its newlines, which hides a
    line-anchored trailer, so its message fields are decoded and scanned
    beside the raw text.
    """
    try:
        with open(path, "rb") as handle:
            data = handle.read(_BODY_FILE_LIMIT + 1)
    except (OSError, ValueError):
        return ""
    if len(data) > _BODY_FILE_LIMIT:
        return ""
    text = data.decode("utf-8", errors="replace")
    if kind == "json":
        try:
            decoded = json.loads(text)
        except ValueError:
            decoded = None
        if isinstance(decoded, (dict, list)):
            text = "\n".join([text] + _strings(decoded, _MESSAGE_FIELDS))
    return text


def detect(text, exempt_provenance=False):
    """Return the label of the first attribution form in text, else "".

    By default every line is judged, which is right for any text published as
    a message (a commit, a pull request, a comment) since it can never be docs
    frontmatter. exempt_provenance=True ignores the session-permalink form on
    every `session-link:` line, for a caller that already knows the text is
    the frontmatter of a Markdown file under docs/; detect_in_payload decides
    that itself and exempts only the lines that qualify.
    """
    if not text:
        return ""
    exempt_subject = None
    for label, pattern in _COMPILED:
        subject = text
        if exempt_provenance and label in _PROVENANCE_EXEMPT:
            if exempt_subject is None:
                exempt_subject = _without_provenance_lines(text)
            subject = exempt_subject
        if pattern.search(subject):
            return label
    return ""


def _line_is_attribution(line):
    for _, pattern in _COMPILED:
        if pattern.search(line):
            return True
    return False


def strip(text):
    """Return text with every attribution line removed.

    Attribution always occupies whole lines (a trailer, a footer, a byline),
    so removal is line-oriented: a line that matches any form is dropped
    whole. Removing a footer usually leaves an orphaned horizontal rule and a
    run of blank lines at the end, so those are cleaned up too. A trailing
    newline is preserved when the input had one, which is what a commit
    message file expects.
    """
    if not text:
        return text
    had_trailing_newline = text.endswith("\n")
    kept = [line for line in text.split("\n") if not _line_is_attribution(line)]
    # Drop blank lines and an orphaned rule left at the end by the removal.
    while kept and (
        kept[-1].strip() == "" or re.fullmatch(r"\s*(?:-{3,}|\*{3,}|_{3,})\s*", kept[-1])
    ):
        kept.pop()
    result = "\n".join(kept)
    if had_trailing_newline and result:
        result += "\n"
    return result


def detect_in_payload(payload):
    """Return the attribution label for a PreToolUse payload, else "".

    Write, Edit, and NotebookEdit are scanned on their authored-text fields;
    a `session-link:` line is exempt from the session-permalink form only in
    a Write or Edit to a Markdown file under docs/, and only when the line
    sits inside that file's leading frontmatter once the write lands.
    Bash is scanned on its command, and only when that command publishes text;
    a file the command names as its message body (gh --body-file, -F
    body=@<path>, --field body=@<path>, gh api --input, git commit -F or
    --file) is read and scanned with it, relative to the payload's cwd, and a
    file that cannot be read contributes nothing. Any other tool (a GitHub
    writer from any MCP server, for instance) is scanned on the message-shaped
    fields of its input, one level deep plus nested objects, so a pull request
    body or an issue comment is covered; local bookkeeping tools are skipped.
    """
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ""
    tool_name = payload.get("tool_name") or ""

    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return _detect_write(tool_name, tool_input)
    if tool_name == "Bash":
        command = tool_input.get("command")
        if not isinstance(command, str) or not _AUTHORING_COMMAND.search(command):
            return ""
        cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else ""
        bodies = [_read_body_file(path, kind) for path, kind in _body_file_paths(command, cwd)]
        return detect("\n".join([command] + [body for body in bodies if body]))
    if tool_name in _LOCAL_TOOLS:
        return ""
    if not tool_name:
        # An unlabeled payload (a bare tool_input, as the tests and the
        # OpenCode bridge send) is judged on every text-bearing field.
        return detect("\n".join(_strings(tool_input, _WRITE_FIELDS + _MESSAGE_FIELDS)))
    return detect("\n".join(_strings(tool_input, _MESSAGE_FIELDS)))


def _strings(value, fields, depth=0):
    """Collect string values stored under fields, recursing into containers."""
    found = []
    if depth > 4:
        return found
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str):
                if key in fields:
                    found.append(item)
            else:
                found.extend(_strings(item, fields, depth + 1))
    elif isinstance(value, list):
        for item in value:
            found.extend(_strings(item, fields, depth + 1))
    return found


def _main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode not in ("detect", "detect-payload", "strip"):
        sys.stderr.write("usage: attribution-detect.py detect|detect-payload|strip\n")
        return 64
    # Bytes in, bytes out. A commit message in a legacy encoding is not UTF-8,
    # and a text-mode stdin raised UnicodeDecodeError on it, which the
    # commit-msg backstop read as clean (review cluster F2). surrogateescape
    # decodes every byte, so the ASCII attribution forms still match, and
    # strip writes each untouched byte back exactly as it came in.
    text = sys.stdin.buffer.read().decode("utf-8", errors="surrogateescape")
    if mode == "strip":
        sys.stdout.buffer.write(strip(text).encode("utf-8", errors="surrogateescape"))
        return 0
    if mode == "detect":
        label = detect(text)
    else:
        try:
            payload = json.loads(text or "{}")
        except ValueError:
            payload = {}
        label = detect_in_payload(payload)
    if label:
        print(label)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
