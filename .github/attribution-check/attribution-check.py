#!/usr/bin/env python3
"""Server-side attribution check for one GitHub event (WI-54, A-02 of
docs/adr/2026-09-23-make-attribution-enforcement-travel-with-the-repository.md).

Runs the detector the local guard uses (hooks/lib/attribution-detect.py) over
what the event published:

  pull_request                 the title, the body, and every commit message
                               (read from --commits, written by the workflow's
                               gh api step, so this script needs no network)
  issue_comment                the comment body
  pull_request_review_comment  the comment body
  push                         each distinct pushed commit's message

Fenced text in a title, body or comment is quoted, not authored, and is
skipped, mirroring the ALLOW_AGENT_ATTRIBUTION exception of
rules/no-agent-attribution.md (quote inside a code fence). An unclosed fence
is not an exemption. Commit messages get no fence exemption: that exception
never reaches a commit message.

Exit status: 0 clean, 1 one line per hit (surface, label, location), 64 a
usage error or an input that could not be read, which is never reported as
clean. The check reports; it never edits, deletes or hides anything.

Usage:
  attribution-check.py [--event-name NAME] [--event-path PATH]
                       [--commits PATH] [--detector PATH]

--event-name and --event-path default to GITHUB_EVENT_NAME and
GITHUB_EVENT_PATH. The detector is found, in order, at --detector, beside this
script, at hooks/lib/ (llm-root) and at .claude/hooks/lib/ (a managed project,
where the carried guard of WI-53 delivers it), each relative to
GITHUB_WORKSPACE or the working directory.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import re
import sys

USAGE = 64
DETECTOR_NAME = "attribution-detect.py"
DETECTOR_PLACES = (
    pathlib.Path("hooks") / "lib" / DETECTOR_NAME,
    pathlib.Path(".claude") / "hooks" / "lib" / DETECTOR_NAME,
)
# Applied after the blockquote markers are removed (_quote_depth).
_FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
_QUOTE_MARKER = re.compile(r"^ {0,3}> ?")


class InputError(Exception):
    """An input that could not be read; never treated as clean."""


def find_detector(explicit: str | None) -> pathlib.Path:
    if explicit:
        path = pathlib.Path(explicit)
        if not path.is_file():
            raise InputError(f"detector not found: {path}")
        return path
    here = pathlib.Path(__file__).resolve().parent
    candidates = [here / DETECTOR_NAME]
    bases = []
    workspace = os.environ.get("GITHUB_WORKSPACE")
    if workspace:
        bases.append(pathlib.Path(workspace))
    bases.append(pathlib.Path.cwd())
    bases.append(here.parent.parent)
    candidates += [base / place for base in bases for place in DETECTOR_PLACES]
    for path in candidates:
        if path.is_file():
            return path
    raise InputError("detector not found: " + ", ".join(str(p) for p in candidates))


def load_detector(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("attribution_detect", path)
    if spec is None or spec.loader is None:
        raise InputError(f"detector cannot be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _quote_depth(line: str) -> tuple[int, str]:
    """(blockquote depth, the rest of the line after the markers)."""
    depth, rest = 0, line
    while True:
        match = _QUOTE_MARKER.match(rest)
        if not match:
            return depth, rest
        depth, rest = depth + 1, rest[match.end():]


def unfenced_lines(text: str) -> list[tuple[int, str]]:
    """(line number, line) for every line outside a closed code fence.

    A fence opens on three or more backticks or tildes and closes on a line
    of the same character at least as long with nothing after it, inside the
    same container. A fence whose container ends first (a blockquote fence
    followed by a line with fewer quote markers, an indented list fence
    followed by a less indented line) is treated as never closed. A fence
    that never closes exempts nothing: its lines are returned as authored.
    This errs toward reporting: an unusual layout that CommonMark would
    render as code is at worst reported, never skipped.
    """
    lines = list(enumerate(text.split("\n"), start=1))
    kept: list[tuple[int, str]] = []
    pending: list[tuple[int, str]] = []
    opener = None  # (fence, quote depth, indent)
    index = 0
    while index < len(lines):
        number, line = lines[index]
        depth, rest = _quote_depth(line)
        match = _FENCE.match(rest)
        if opener is None:
            if match and not (match.group(2)[0] == "`" and "`" in match.group(3)):
                opener = (match.group(2), depth, len(match.group(1)))
                pending = [(number, line)]
            else:
                kept.append((number, line))
            index += 1
            continue
        fence, open_depth, indent = opener
        leading = len(rest) - len(rest.lstrip(" "))
        if depth < open_depth or (indent and rest.strip() and leading < indent):
            # The container ended before the fence closed: nothing exempt,
            # and this line is judged again outside the fence.
            kept.extend(pending)
            opener, pending = None, []
            continue
        pending.append((number, line))
        if (
            match
            and depth == open_depth
            and match.group(2)[0] == fence[0]
            and len(match.group(2)) >= len(fence)
            and not match.group(3).strip()
        ):
            opener, pending = None, []
        index += 1
    return sorted(kept + pending)


def scan(detector, surface: str, text, fenced_exempt: bool, suffix: str = "") -> list[str]:
    """One report line per attribution hit in text."""
    if not isinstance(text, str) or not text:
        return []
    if fenced_exempt:
        lines = unfenced_lines(text)
    else:
        lines = list(enumerate(text.split("\n"), start=1))
    whole = "\n".join(line for _, line in lines)
    if not _detect(detector, whole):
        return []
    hits = []
    for number, line in lines:
        label = _detect(detector, line)
        if label:
            hits.append(f"{surface}: {label} at line {number}{suffix}")
    if not hits:
        # A form that spans lines: report it on the surface as a whole.
        hits.append(f"{surface}: {_detect(detector, whole)} in the text{suffix}")
    return hits


def _detect(detector, text: str) -> str:
    """detect() without the docs frontmatter exemption: a published message
    is never docs frontmatter, so a session-link line in it is a hit."""
    try:
        return detector.detect(text, exempt_provenance=False)
    except TypeError as error:
        raise InputError("detector predates exempt_provenance; sync the carried guard") from error


def read_json(path: str, what: str):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise InputError(f"{what} unreadable: {path}: {error}") from error


def read_commits(path: str | None) -> list[tuple[str, str]]:
    """(sha, message) pairs from a JSON array of API commits or JSON lines."""
    if not path:
        raise InputError("pull_request needs --commits (the pull request's commits from the API)")
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise InputError(f"commits unreadable: {path}: {error}") from error
    try:
        items = json.loads(text) if text.strip() else []
        if isinstance(items, dict):
            items = [items]
    except ValueError:
        try:
            items = [json.loads(line) for line in text.splitlines() if line.strip()]
        except ValueError as error:
            raise InputError(f"commits unreadable: {path}: {error}") from error
    if not isinstance(items, list):
        raise InputError(f"commits unreadable: {path}: not a list")
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise InputError(f"commits unreadable: {path}: an entry is not an object")
        message = item.get("message")
        if message is None and isinstance(item.get("commit"), dict):
            message = item["commit"].get("message")
        out.append((str(item.get("sha") or item.get("id") or "unknown"), message or ""))
    return out


def check(event_name: str, payload: dict, commits_path: str | None, detector) -> list[str]:
    hits: list[str] = []
    if event_name == "pull_request":
        pr = payload.get("pull_request") or {}
        hits += scan(detector, "pull_request.title", pr.get("title"), fenced_exempt=True)
        hits += scan(detector, "pull_request.body", pr.get("body"), fenced_exempt=True)
        for sha, message in read_commits(commits_path):
            hits += scan(detector, f"commit {sha[:12]}", message, fenced_exempt=False)
    elif event_name in ("issue_comment", "pull_request_review_comment"):
        comment = payload.get("comment") or {}
        url = comment.get("html_url")
        suffix = f" ({url})" if url else ""
        hits += scan(detector, f"{event_name}.body", comment.get("body"), fenced_exempt=True, suffix=suffix)
    elif event_name == "push":
        for commit in payload.get("commits") or []:
            if not isinstance(commit, dict) or commit.get("distinct") is False:
                continue
            sha = str(commit.get("id") or "unknown")
            hits += scan(detector, f"commit {sha[:12]}", commit.get("message"), fenced_exempt=False)
    else:
        raise InputError(f"unhandled event: {event_name or '(none)'}")
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    parser.add_argument("--event-path", default=os.environ.get("GITHUB_EVENT_PATH", ""))
    parser.add_argument("--commits")
    parser.add_argument("--detector")
    args = parser.parse_args(argv)
    try:
        if not args.event_path:
            raise InputError("no event payload: pass --event-path or set GITHUB_EVENT_PATH")
        payload = read_json(args.event_path, "event payload")
        if not isinstance(payload, dict):
            raise InputError("event payload is not an object")
        detector = load_detector(find_detector(args.detector))
        hits = check(args.event_name, payload, args.commits, detector)
    except InputError as error:
        print(f"attribution-check: error: {error}", file=sys.stderr)
        return USAGE
    for hit in hits:
        print(f"attribution-check: {hit}")
        print(f"::error title=attribution-check::{hit}")
    if hits:
        print(f"attribution-check: {len(hits)} hit(s); see rules/no-agent-attribution.md")
        return 1
    print(f"attribution-check: {args.event_name} clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
