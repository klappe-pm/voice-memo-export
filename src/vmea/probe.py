"""VMEA Probe: find the Voice Memos audio folder and explain what was found.

The probe runs in layers, and every layer is a plain function that takes its filesystem and
subprocess calls through a `ProbeEnv`, so the whole thing is tested on Linux with fixture folders.

1. Each known path gets one of four states: missing, readable, blocked or empty. Blocked means
   listing the folder raised an error, which on macOS means Full Disk Access is not granted.
2. When no known path is readable, Spotlight (`mdfind`) is asked for other candidate folders.
3. The readable folder with the most recordings wins, and the result is explained in plain words.
   Two or more distinct readable folders are flagged as ambiguous.
4. A blocked folder comes with the System Settings link and the interpreter to add.
5. A newest recording older than a threshold produces iCloud sync steps.

Nothing here prompts, opens System Settings, changes a permission or writes a file. Symlinks are
never followed out of a folder, and every scan is bounded.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo
from enum import StrEnum
from pathlib import Path
from typing import Any

from vmea import discovery

AUDIO_SUFFIXES = (".m4a", ".qta")
"""Audio file types Voice Memos writes. `.qta` is the QuickTime audio form used by newer macOS."""

MAX_ENTRIES = 50_000
"""Most directory entries examined per folder before the scan stops and reports truncation."""

MAX_SPOTLIGHT_HITS = 2_000
"""Most `mdfind` output lines read per query."""

MAX_SPOTLIGHT_FOLDERS = 25
"""Most candidate folders probed after a Spotlight search."""

DEFAULT_STALE_DAYS = 7
"""A newest recording older than this many days triggers the iCloud sync steps."""

SPOTLIGHT_TIMEOUT_SECONDS = 10.0
"""Longest a single `mdfind` call may run."""

MDFIND_PATH = "/usr/bin/mdfind"
"""The Spotlight command line program, called by absolute path and never found through PATH."""

FULL_DISK_ACCESS_URL = "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
"""Opens the Full Disk Access pane of System Settings."""

SECONDS_PER_DAY = 86_400


@dataclass(frozen=True)
class Entry:
    """One directory entry, reduced to what the probe needs."""

    name: str
    is_regular: bool
    """True only for a regular file. A symlink is never regular, so it is never followed."""
    mtime: float | None = None
    """Modification time. Only filled in for regular audio files."""


Lister = Callable[[Path, int], tuple[list[Entry], bool]]
"""Takes a folder and an entry limit, returns the entries and whether the limit cut the scan."""

Runner = Callable[[Sequence[str], float], str]
"""Takes a command and a timeout in seconds, returns standard output, raises on failure."""


def is_audio_name(name: str) -> bool:
    """Return True for a recording file name.

    Names that start with a dot are skipped: they are AppleDouble resource forks and iCloud
    placeholders, not recordings.
    """
    return not name.startswith(".") and name.lower().endswith(AUDIO_SUFFIXES)


def _entry_from(dirent: os.DirEntry[str]) -> Entry:
    """Reduce a `DirEntry` to an `Entry` without following symlinks."""
    try:
        regular = dirent.is_file(follow_symlinks=False)
    except OSError:
        return Entry(dirent.name, False)
    mtime: float | None = None
    if regular and is_audio_name(dirent.name):
        try:
            mtime = dirent.stat(follow_symlinks=False).st_mtime
        except OSError:
            return Entry(dirent.name, False)
    return Entry(dirent.name, regular, mtime)


def scan_entries(path: Path, limit: int = MAX_ENTRIES) -> tuple[list[Entry], bool]:
    """List one folder, never following symlinks and never reading more than `limit` entries.

    Raises the OS error from listing, such as `PermissionError`. The scan is not recursive.
    """
    entries: list[Entry] = []
    with os.scandir(path) as iterator:
        for seen, dirent in enumerate(iterator):
            if seen >= limit:
                return entries, True
            entries.append(_entry_from(dirent))
    return entries, False


def run_command(args: Sequence[str], timeout: float) -> str:
    """Run a command with a timeout and return its standard output.

    Raises `subprocess.TimeoutExpired`, `subprocess.CalledProcessError` or `OSError` on failure.
    """
    result = subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=True,
    )
    return result.stdout


def locate_mdfind() -> str | None:
    """Return the path of `mdfind` if it can be run, else None (as on Linux)."""
    return MDFIND_PATH if os.access(MDFIND_PATH, os.X_OK) else None


def resolve_path(path: Path) -> Path:
    """Resolve symlinks for comparison, returning the input if resolving fails."""
    try:
        return path.resolve()
    except (OSError, RuntimeError):
        return path


@dataclass(frozen=True)
class ProbeEnv:
    """The outside world, injectable so the probe can be tested anywhere."""

    lister: Lister = scan_entries
    runner: Runner = run_command
    find_mdfind: Callable[[], str | None] | None = None
    """Defaults to `locate_mdfind`, looked up when used so it can be patched."""
    resolve: Callable[[Path], Path] = resolve_path
    now: Callable[[], float] = time.time
    tz: tzinfo | None = None
    """Time zone for describing times. None means the local zone."""
    home: Path | None = None
    """Folder Spotlight is limited to. None means the user's home folder."""
    max_entries: int = MAX_ENTRIES
    spotlight_timeout: float = SPOTLIGHT_TIMEOUT_SECONDS


class PathState(StrEnum):
    """What probing one folder found."""

    MISSING = "missing"
    """Nothing is there, or it is not a folder."""
    READABLE = "readable"
    """The folder can be listed and holds at least one recording."""
    BLOCKED = "blocked"
    """The folder exists but listing it failed. On macOS this means Full Disk Access."""
    EMPTY = "empty"
    """The folder can be listed and holds no recording."""


@dataclass(frozen=True)
class PathProbe:
    """The result of probing one folder."""

    path: Path
    """The path with `~` expanded."""
    state: PathState
    memo_count: int = 0
    newest_mtime: float | None = None
    newest_text: str | None = None
    """The newest recording's time in plain words, such as `yesterday 4:12 pm`."""
    truncated: bool = False
    """True when the scan hit its entry limit, so the count is a lower bound."""
    detail: str | None = None
    """The OS error text for a missing or blocked folder."""
    source: str = "known"
    """Where the folder came from: `known` or `spotlight`."""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON ready dictionary."""
        newest = (
            datetime.fromtimestamp(self.newest_mtime, UTC).isoformat()
            if self.newest_mtime is not None
            else None
        )
        return {
            "path": str(self.path),
            "state": self.state.value,
            "memo_count": self.memo_count,
            "newest": newest,
            "newest_text": self.newest_text,
            "truncated": self.truncated,
            "detail": self.detail,
            "source": self.source,
        }


def describe_time(timestamp: float, now: float, tz: tzinfo | None = None) -> str:
    """Describe a time in plain words, such as `yesterday 4:12 pm` or `Tue 3 Oct 9:05 am`."""
    moment = datetime.fromtimestamp(timestamp, tz)
    today = datetime.fromtimestamp(now, tz).date()
    suffix = "am" if moment.hour < 12 else "pm"
    clock = f"{moment.hour % 12 or 12}:{moment.minute:02d} {suffix}"
    days = (today - moment.date()).days
    if days == 0:
        day = "today"
    elif days == 1:
        day = "yesterday"
    elif moment.year == today.year:
        day = f"{moment:%a} {moment.day} {moment:%b}"
    else:
        day = f"{moment:%a} {moment.day} {moment:%b} {moment.year}"
    return f"{day} {clock}"


def _reason(exc: OSError) -> str:
    return exc.strerror or type(exc).__name__


def probe_path(path: Path, env: ProbeEnv | None = None, *, source: str = "known") -> PathProbe:
    """Probe one folder and report which of the four states it is in.

    The folder is listed rather than tested with `exists`, because on macOS a folder that Full
    Disk Access protects can look present while listing it raises a permission error. That is
    `BLOCKED`, never `MISSING` or `EMPTY`.
    """
    env = env or ProbeEnv()
    expanded = path.expanduser()
    try:
        entries, truncated = env.lister(expanded, env.max_entries)
    except (FileNotFoundError, NotADirectoryError) as exc:
        return PathProbe(expanded, PathState.MISSING, detail=_reason(exc), source=source)
    except OSError as exc:
        # PermissionError is the Full Disk Access case. Any other failure to list a folder that
        # is there is blocked too: it exists and cannot be read.
        return PathProbe(expanded, PathState.BLOCKED, detail=_reason(exc), source=source)
    audio = [e for e in entries if e.is_regular and is_audio_name(e.name)]
    if not audio:
        return PathProbe(expanded, PathState.EMPTY, truncated=truncated, source=source)
    newest = max((e.mtime for e in audio if e.mtime is not None), default=None)
    return PathProbe(
        expanded,
        PathState.READABLE,
        memo_count=len(audio),
        newest_mtime=newest,
        newest_text=describe_time(newest, env.now(), env.tz) if newest is not None else None,
        truncated=truncated,
        source=source,
    )


def rank_readable(probes: Iterable[PathProbe], env: ProbeEnv | None = None) -> list[PathProbe]:
    """Return the readable folders, best first.

    Order is most recordings, then newest recording, then path. Two paths that resolve to the
    same folder count once, so a symlinked alias is not a second candidate.
    """
    env = env or ProbeEnv()
    readable = [p for p in probes if p.state is PathState.READABLE]
    readable.sort(key=lambda p: (-p.memo_count, -(p.newest_mtime or 0.0), str(p.path)))
    distinct: list[PathProbe] = []
    seen: set[Path] = set()
    for item in readable:
        key = env.resolve(item.path)
        if key not in seen:
            seen.add(key)
            distinct.append(item)
    return distinct


class SpotlightStatus(StrEnum):
    """How the Spotlight search went."""

    OK = "ok"
    SKIPPED = "skipped"
    ABSENT = "absent"
    """`mdfind` is not available, as on Linux."""
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True)
class SpotlightResult:
    """Candidate folders from Spotlight, and how the search went."""

    status: SpotlightStatus
    folders: tuple[Path, ...] = ()
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON ready dictionary."""
        return {
            "status": self.status.value,
            "folders": [str(p) for p in self.folders],
            "detail": self.detail,
        }


def _looks_like_voice_memos(path: Path) -> bool:
    text = f"{path}/".lower()
    return "voicememos" in text or "voice memos" in text or "/recordings/" in text


def _spotlight_queries(onlyin: Path | None) -> list[tuple[str, list[str]]]:
    scope = ["-onlyin", str(onlyin)] if onlyin is not None else []
    audio = (
        '(kMDItemFSName == "*.m4a"c || kMDItemFSName == "*.qta"c) && '
        '(kMDItemPath == "*VoiceMemos*"c || kMDItemPath == "*Voice Memos*"c '
        '|| kMDItemPath == "*/Recordings/*"c)'
    )
    return [
        ("database", [*scope, "-name", "CloudRecordings.db"]),
        ("audio", [*scope, audio]),
    ]


def _home(env: ProbeEnv) -> Path | None:
    if env.home is not None:
        return env.home
    try:
        return Path.home()
    except RuntimeError:  # pragma: no cover (no home folder can be determined)
        return None


def spotlight_search(env: ProbeEnv | None = None) -> SpotlightResult:
    """Ask Spotlight for folders that may hold Voice Memos recordings.

    Two queries run, one for the `CloudRecordings.db` database and one for audio files under a
    Voice Memos or Recordings style folder. The parent folder of each hit is returned once, in
    the order found. The call is bounded by a timeout and a hit limit, and a missing `mdfind`
    gives `ABSENT` instead of an error. The queries are inferred, not checked against a real
    Spotlight index.
    """
    env = env or ProbeEnv()
    mdfind = (env.find_mdfind or locate_mdfind)()
    if mdfind is None:
        return SpotlightResult(SpotlightStatus.ABSENT, detail="mdfind is not available here")
    folders: list[Path] = []
    for kind, args in _spotlight_queries(_home(env)):
        try:
            output = env.runner([mdfind, *args], env.spotlight_timeout)
        except subprocess.TimeoutExpired:
            return SpotlightResult(
                SpotlightStatus.TIMEOUT,
                tuple(folders),
                f"mdfind took longer than {env.spotlight_timeout:g} seconds",
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return SpotlightResult(SpotlightStatus.ERROR, tuple(folders), str(exc))
        for line in output.splitlines()[:MAX_SPOTLIGHT_HITS]:
            hit = Path(line.strip())
            if not line.strip() or not hit.is_absolute() or ".Trash" in hit.parts:
                continue
            if kind == "audio" and not (
                is_audio_name(hit.name) and _looks_like_voice_memos(hit.parent)
            ):
                continue
            parent = hit.parent
            if parent not in folders and len(folders) < MAX_SPOTLIGHT_FOLDERS:
                folders.append(parent)
    return SpotlightResult(SpotlightStatus.OK, tuple(folders))


@dataclass(frozen=True)
class FullDiskAccessHelp:
    """What the user needs to grant Full Disk Access."""

    needed: bool
    """True when at least one folder was blocked."""
    url: str
    interpreter: str
    """The resolved interpreter to add in System Settings."""
    steps: tuple[str, ...]
    launchd_note: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON ready dictionary."""
        return {
            "needed": self.needed,
            "url": self.url,
            "interpreter": self.interpreter,
            "steps": list(self.steps),
            "launchd_note": self.launchd_note,
        }


def full_disk_access_help(
    *, needed: bool = True, executable: str | None = None, env: ProbeEnv | None = None
) -> FullDiskAccessHelp:
    """Return the Full Disk Access link, the interpreter to add and the steps.

    macOS ties the permission to the real program, so the interpreter is resolved through any
    virtual environment symlink before it is shown.
    """
    env = env or ProbeEnv()
    interpreter = str(env.resolve(Path(executable or sys.executable)))
    steps = (
        f'Open the Full Disk Access pane: run open "{FULL_DISK_ACCESS_URL}", or open System '
        "Settings, then Privacy & Security, then Full Disk Access.",
        f"Click the plus button and add this interpreter: {interpreter}. In the file picker, "
        "press Command Shift G and paste the path.",
        "If you run vmea from a terminal, also turn on that terminal app, such as Terminal or "
        "iTerm, because macOS checks the app that started the command.",
        "Switch each entry on, quit and reopen the terminal, then run vmea probe again.",
    )
    note = (
        "The background agent from vmea daemon install runs the interpreter that was active "
        "when you installed it. If that is a different Python, add that interpreter as well."
    )
    return FullDiskAccessHelp(needed, FULL_DISK_ACCESS_URL, interpreter, steps, note)


@dataclass(frozen=True)
class Freshness:
    """Whether the newest recording is recent enough to trust the sync."""

    stale: bool
    age_days: float
    threshold_days: int
    message: str
    steps: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON ready dictionary."""
        return {
            "stale": self.stale,
            "age_days": round(self.age_days, 2),
            "threshold_days": self.threshold_days,
            "message": self.message,
            "steps": list(self.steps),
        }


ICLOUD_STEPS = (
    "On your iPhone, open Settings, tap your name, tap iCloud, tap Show All, and turn on "
    "Voice Memos.",
    "On your Mac, open System Settings, click your name, click iCloud, and turn on Voice Memos.",
    "Use the same Apple Account on both devices and stay on Wi-Fi.",
    "Open the Voice Memos app on the Mac and leave it open for a minute so it can catch up.",
    "Record a short test memo on your iPhone, then run vmea probe again to see if it arrives.",
)


def check_freshness(newest_mtime: float, now: float, stale_days: int) -> Freshness:
    """Say whether the newest recording is older than `stale_days`, with iCloud steps if so."""
    age_days = (now - newest_mtime) / SECONDS_PER_DAY
    if age_days > stale_days:
        whole = int(age_days)
        unit = "day" if whole == 1 else "days"
        message = (
            f"The newest recording is {whole} {unit} old, which is more than {stale_days} "
            "days. If you have recorded something newer, it may not be syncing to this Mac."
        )
        return Freshness(True, age_days, stale_days, message, ICLOUD_STEPS)
    return Freshness(False, age_days, stale_days, "Sync looks current.")


@dataclass(frozen=True)
class ProbeReport:
    """Everything the probe learned, ready to print or serialise."""

    known: tuple[PathProbe, ...]
    spotlight: SpotlightResult
    found: tuple[PathProbe, ...]
    """Probes of the folders Spotlight suggested. Empty unless Spotlight ran."""
    chosen: PathProbe | None
    alternatives: tuple[PathProbe, ...]
    """Other distinct readable folders, best first."""
    ambiguous: bool
    ambiguity: str | None
    summary: str
    freshness: Freshness | None
    full_disk_access: FullDiskAccessHelp

    @property
    def blocked(self) -> bool:
        """True when any probed folder was blocked."""
        return any(p.state is PathState.BLOCKED for p in (*self.known, *self.found))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON ready dictionary."""
        return {
            "chosen": self.chosen.to_dict() if self.chosen else None,
            "summary": self.summary,
            "ambiguous": self.ambiguous,
            "ambiguity": self.ambiguity,
            "alternatives": [p.to_dict() for p in self.alternatives],
            "known": [p.to_dict() for p in self.known],
            "spotlight": self.spotlight.to_dict(),
            "found": [p.to_dict() for p in self.found],
            "freshness": self.freshness.to_dict() if self.freshness else None,
            "full_disk_access": self.full_disk_access.to_dict(),
        }


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _summarize(chosen: PathProbe | None, probes: Sequence[PathProbe]) -> str:
    if chosen is not None:
        count = _plural(chosen.memo_count, "recording")
        if chosen.truncated:
            count = f"at least {count}"
        text = f"Found {count}"
        return f"{text}, newest from {chosen.newest_text}" if chosen.newest_text else text
    states = {p.state for p in probes}
    if PathState.BLOCKED in states:
        return (
            "Found a Voice Memos folder, but macOS will not let this program read it. "
            "Full Disk Access is needed."
        )
    if PathState.EMPTY in states:
        return "Found a Voice Memos folder, but it holds no recordings yet."
    return "No Voice Memos folder was found in the usual places."


def _describe_ambiguity(chosen: PathProbe, alternatives: Sequence[PathProbe]) -> str:
    others = ", ".join(f"{p.path} ({_plural(p.memo_count, 'recording')})" for p in alternatives)
    return (
        f"{len(alternatives) + 1} folders look plausible. Chose {chosen.path} "
        f"({_plural(chosen.memo_count, 'recording')}), which has the most recordings. "
        f"Others: {others}. Confirm it is the right one."
    )


def run_probe(
    paths: Iterable[Path] | None = None,
    *,
    spotlight: bool = True,
    stale_days: int = DEFAULT_STALE_DAYS,
    env: ProbeEnv | None = None,
    executable: str | None = None,
) -> ProbeReport:
    """Probe the known folders, fall back to Spotlight, choose one and explain.

    With no `paths` the entries in `discovery.VOICE_MEMOS_PATHS` are probed. Spotlight only runs
    when no known folder is readable, and only if `spotlight` is true.
    """
    env = env or ProbeEnv()
    candidates = list(paths) if paths is not None else list(discovery.VOICE_MEMOS_PATHS)
    known = tuple(probe_path(p, env) for p in candidates)
    ranked = rank_readable(known, env)
    found: tuple[PathProbe, ...] = ()
    if ranked:
        result = SpotlightResult(SpotlightStatus.SKIPPED, detail="a known folder is readable")
    elif not spotlight:
        result = SpotlightResult(SpotlightStatus.SKIPPED, detail="turned off")
    else:
        result = spotlight_search(env)
        known_keys = {env.resolve(p.path) for p in known}
        found = tuple(
            probe_path(folder, env, source="spotlight")
            for folder in result.folders
            if env.resolve(folder.expanduser()) not in known_keys
        )
        ranked = rank_readable(found, env)
    chosen = ranked[0] if ranked else None
    alternatives = tuple(ranked[1:])
    ambiguous = chosen is not None and bool(alternatives)
    return ProbeReport(
        known=known,
        spotlight=result,
        found=found,
        chosen=chosen,
        alternatives=alternatives,
        ambiguous=ambiguous,
        ambiguity=_describe_ambiguity(chosen, alternatives) if chosen and alternatives else None,
        summary=_summarize(chosen, (*known, *found)),
        freshness=(
            check_freshness(chosen.newest_mtime, env.now(), stale_days)
            if chosen is not None and chosen.newest_mtime is not None
            else None
        ),
        full_disk_access=full_disk_access_help(
            needed=any(p.state is PathState.BLOCKED for p in (*known, *found)),
            executable=executable,
            env=env,
        ),
    )
