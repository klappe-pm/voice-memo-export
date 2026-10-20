"""Tests for the layered audio folder probe, run on fixture folders so Linux CI covers it."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from vmea import discovery, probe
from vmea.probe import (
    Entry,
    PathProbe,
    PathState,
    ProbeEnv,
    SpotlightResult,
    SpotlightStatus,
    _entry_from,
    check_freshness,
    describe_time,
    full_disk_access_help,
    is_audio_name,
    probe_path,
    rank_readable,
    resolve_path,
    run_command,
    run_probe,
    scan_entries,
    spotlight_search,
)
from vmea.probe import locate_mdfind as real_locate_mdfind

DAY = 86_400


def stamp(day: int, hour: int, minute: int, month: int = 10, year: int = 2026) -> float:
    return datetime(year, month, day, hour, minute, tzinfo=UTC).timestamp()


NOW = stamp(20, 12, 0)
YESTERDAY_412PM = stamp(19, 16, 12)


def make_env(**kwargs: Any) -> ProbeEnv:
    """An environment with a pinned clock and time zone."""
    return ProbeEnv(now=lambda: NOW, tz=UTC, **kwargs)


def make_folder(folder: Path, names: list[str], mtime: float = YESTERDAY_412PM) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        file = folder / name
        file.write_bytes(b"audio")
        os.utime(file, (mtime, mtime))
    return folder


def blocking_lister(*blocked: Path):
    """A lister that raises PermissionError for the given folders, as macOS does."""

    def lister(path: Path, limit: int) -> tuple[list[Entry], bool]:
        if path in blocked:
            raise PermissionError(1, "Operation not permitted")
        return scan_entries(path, limit)

    return lister


def raising_lister(exc: Exception):
    def lister(_path: Path, _limit: int) -> tuple[list[Entry], bool]:
        raise exc

    return lister


# is_audio_name


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("a.m4a", True),
        ("A.M4A", True),
        ("b.qta", True),
        ("note.txt", False),
        ("._a.m4a", False),
        (".a.m4a.icloud", False),
        ("a.composition", False),
    ],
)
def test_is_audio_name(name: str, expected: bool) -> None:
    assert is_audio_name(name) is expected


# probe_path: the four states


def test_readable_counts_audio_and_reports_newest(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", ["a.m4a", "b.QTA"], stamp(18, 9, 5))
    newest = folder / "c.m4a"
    newest.write_bytes(b"x")
    os.utime(newest, (YESTERDAY_412PM, YESTERDAY_412PM))
    (folder / "notes.txt").write_text("not audio")
    (folder / "d.composition").mkdir()
    (folder / "._e.m4a").write_bytes(b"fork")
    (folder / ".f.m4a.icloud").write_bytes(b"placeholder")

    result = probe_path(folder, make_env())

    assert result.state is PathState.READABLE
    assert result.memo_count == 3
    assert result.newest_mtime == YESTERDAY_412PM
    assert result.newest_text == "yesterday 4:12 pm"
    assert result.detail is None
    assert result.truncated is False


def test_missing_path(tmp_path: Path) -> None:
    result = probe_path(tmp_path / "nope", make_env())

    assert result.state is PathState.MISSING
    assert result.memo_count == 0
    assert result.detail


def test_a_file_where_a_folder_should_be_is_missing(tmp_path: Path) -> None:
    file = tmp_path / "Recordings"
    file.write_bytes(b"x")

    assert probe_path(file, make_env()).state is PathState.MISSING


def test_empty_folder(tmp_path: Path) -> None:
    folder = tmp_path / "Recordings"
    folder.mkdir()

    result = probe_path(folder, make_env())

    assert result.state is PathState.EMPTY
    assert result.memo_count == 0
    assert result.newest_mtime is None


def test_folder_without_audio_is_empty(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", ["notes.txt", "readme.md"])

    assert probe_path(folder, make_env()).state is PathState.EMPTY


def test_permission_error_is_blocked_not_empty() -> None:
    env = make_env(lister=raising_lister(PermissionError(1, "Operation not permitted")))

    result = probe_path(Path("/blocked"), env)

    assert result.state is PathState.BLOCKED
    assert result.detail == "Operation not permitted"


def test_blocked_without_message_uses_the_error_name() -> None:
    result = probe_path(Path("/blocked"), make_env(lister=raising_lister(PermissionError())))

    assert result.state is PathState.BLOCKED
    assert result.detail == "PermissionError"


def test_other_os_errors_are_blocked() -> None:
    result = probe_path(Path("/x"), make_env(lister=raising_lister(OSError(5, "I/O error"))))

    assert result.state is PathState.BLOCKED
    assert result.detail == "I/O error"


def test_blocked_through_the_real_lister(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Running as root ignores chmod, so make os.scandir raise as macOS does."""
    folder = make_folder(tmp_path / "Recordings", ["a.m4a"])
    real = os.scandir

    def fake(path: Any) -> Any:
        if Path(path) == folder:
            raise PermissionError(1, "Operation not permitted")
        return real(path)

    monkeypatch.setattr(probe.os, "scandir", fake)

    assert probe_path(folder).state is PathState.BLOCKED


def test_tilde_is_expanded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    make_folder(tmp_path / "Recordings", ["a.m4a"])

    result = probe_path(Path("~/Recordings"), make_env())

    assert result.path == tmp_path / "Recordings"
    assert result.state is PathState.READABLE


def test_source_is_recorded(tmp_path: Path) -> None:
    assert probe_path(tmp_path, make_env(), source="spotlight").source == "spotlight"
    assert probe_path(tmp_path / "x", make_env(), source="spotlight").source == "spotlight"


# Symlinks and bounds


def test_symlinks_out_of_the_folder_are_not_followed(tmp_path: Path) -> None:
    outside = make_folder(tmp_path / "outside", ["x.m4a", "y.m4a", "z.m4a"])
    folder = make_folder(tmp_path / "Recordings", ["real.m4a"])
    (folder / "escape.m4a").symlink_to(outside / "x.m4a")
    (folder / "escape-dir").symlink_to(outside, target_is_directory=True)

    result = probe_path(folder, make_env())

    assert result.state is PathState.READABLE
    assert result.memo_count == 1


def test_a_folder_of_only_symlinks_is_empty(tmp_path: Path) -> None:
    outside = make_folder(tmp_path / "outside", ["x.m4a"])
    folder = tmp_path / "Recordings"
    folder.mkdir()
    (folder / "escape.m4a").symlink_to(outside / "x.m4a")

    assert probe_path(folder, make_env()).state is PathState.EMPTY


def test_scan_entries_marks_symlinks_irregular(tmp_path: Path) -> None:
    outside = make_folder(tmp_path / "outside", ["x.m4a"])
    folder = make_folder(tmp_path / "Recordings", ["real.m4a"])
    (folder / "link.m4a").symlink_to(outside / "x.m4a")

    entries, truncated = scan_entries(folder)
    by_name = {e.name: e for e in entries}

    assert truncated is False
    assert by_name["real.m4a"].is_regular
    assert by_name["real.m4a"].mtime is not None
    assert not by_name["link.m4a"].is_regular
    assert by_name["link.m4a"].mtime is None


def test_scan_is_bounded(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", [f"{i}.m4a" for i in range(10)])

    result = probe_path(folder, make_env(max_entries=4))

    assert result.state is PathState.READABLE
    assert result.memo_count == 4
    assert result.truncated is True


def test_scan_at_exactly_the_limit_is_not_truncated(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", [f"{i}.m4a" for i in range(4)])

    result = probe_path(folder, make_env(max_entries=4))

    assert result.memo_count == 4
    assert result.truncated is False


def test_a_truncated_folder_with_no_audio_is_empty_and_truncated(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", [f"{i}.txt" for i in range(6)])

    result = probe_path(folder, make_env(max_entries=2))

    assert result.state is PathState.EMPTY
    assert result.truncated is True


class FakeDirEntry:
    name = "a.m4a"

    def __init__(self, is_file_error: bool = False, stat_error: bool = False) -> None:
        self.is_file_error = is_file_error
        self.stat_error = stat_error

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        assert follow_symlinks is False, "the probe must never follow symlinks"
        if self.is_file_error:
            raise OSError("gone")
        return True

    def stat(self, *, follow_symlinks: bool = True) -> Any:
        assert follow_symlinks is False, "the probe must never follow symlinks"
        if self.stat_error:
            raise OSError("gone")
        raise AssertionError("not reached")


def test_entry_that_vanishes_during_the_scan_is_ignored() -> None:
    assert _entry_from(cast(Any, FakeDirEntry(is_file_error=True))).is_regular is False
    assert _entry_from(cast(Any, FakeDirEntry(stat_error=True))).is_regular is False


# Ranking


def readable(path: str, count: int, newest: float | None = None) -> PathProbe:
    return PathProbe(Path(path), PathState.READABLE, memo_count=count, newest_mtime=newest)


def test_rank_by_count_then_newest_then_path() -> None:
    probes = [
        readable("/b", 5, 100.0),
        readable("/a", 5, 100.0),
        readable("/c", 5, 200.0),
        readable("/d", 9, 1.0),
        PathProbe(Path("/e"), PathState.BLOCKED),
        PathProbe(Path("/f"), PathState.EMPTY),
        PathProbe(Path("/g"), PathState.MISSING),
    ]

    ranked = rank_readable(probes, make_env(resolve=lambda p: p))

    assert [str(p.path) for p in ranked] == ["/d", "/c", "/a", "/b"]


def test_rank_treats_missing_newest_as_oldest() -> None:
    ranked = rank_readable(
        [readable("/a", 5, None), readable("/b", 5, 10.0)], make_env(resolve=lambda p: p)
    )

    assert [str(p.path) for p in ranked] == ["/b", "/a"]


def test_rank_counts_two_paths_to_one_folder_once(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", ["a.m4a", "b.m4a"])
    alias = tmp_path / "alias"
    alias.symlink_to(folder, target_is_directory=True)
    env = make_env()

    ranked = rank_readable([probe_path(folder, env), probe_path(alias, env)], env)

    assert len(ranked) == 1


def test_rank_without_an_env() -> None:
    assert rank_readable([readable("/a", 1)])[0].path == Path("/a")


# Spotlight

HOME = Path("/Users/me")
DB_HIT = "/Users/me/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/CloudRecordings.db"


class Runner:
    """Stand in for the mdfind call. Each query gets the next canned answer."""

    def __init__(self, *answers: str | Exception) -> None:
        self.answers = list(answers)
        self.calls: list[tuple[list[str], float]] = []

    def __call__(self, args: Any, timeout: float) -> str:
        self.calls.append((list(args), timeout))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def spotlight_env(runner: Runner, **kwargs: Any) -> ProbeEnv:
    return make_env(runner=runner, find_mdfind=lambda: "/usr/bin/mdfind", home=HOME, **kwargs)


def test_spotlight_is_absent_without_mdfind() -> None:
    runner = Runner()

    result = spotlight_search(make_env(runner=runner, find_mdfind=lambda: None))

    assert result.status is SpotlightStatus.ABSENT
    assert result.folders == ()
    assert runner.calls == []


def test_spotlight_defaults_to_locating_mdfind() -> None:
    """With no finder given, the patched locate_mdfind (None, as on Linux) is used."""
    assert spotlight_search(make_env()).status is SpotlightStatus.ABSENT


def test_spotlight_returns_parent_folders_once_in_order() -> None:
    runner = Runner(
        DB_HIT + "\n",
        "\n".join(
            [
                "/Users/me/Documents/Voice Memos/a.m4a",
                "/Users/me/Music/song.m4a",
                "/Users/me/.Trash/Voice Memos/b.m4a",
                "relative/Voice Memos/c.m4a",
                "",
                "/Users/me/Documents/Voice Memos/a2.m4a",
                "/Users/me/Documents/Voice Memos/notes.txt",
                "/Users/me/Recordings/d.qta",
            ]
        ),
    )

    result = spotlight_search(spotlight_env(runner))

    assert result.status is SpotlightStatus.OK
    assert result.folders == (
        Path(DB_HIT).parent,
        Path("/Users/me/Documents/Voice Memos"),
        Path("/Users/me/Recordings"),
    )


def test_spotlight_queries_are_bounded_and_scoped() -> None:
    runner = Runner("", "")

    spotlight_search(spotlight_env(runner, spotlight_timeout=3.0))

    db_args, audio_args = (call[0] for call in runner.calls)
    assert db_args[:3] == ["/usr/bin/mdfind", "-onlyin", str(HOME)]
    assert db_args[-2:] == ["-name", "CloudRecordings.db"]
    assert audio_args[:3] == ["/usr/bin/mdfind", "-onlyin", str(HOME)]
    assert "kMDItemFSName" in audio_args[-1]
    assert ".qta" in audio_args[-1]
    assert all(call[1] == 3.0 for call in runner.calls)


def test_spotlight_defaults_to_the_home_folder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/Users/someone")
    runner = Runner("", "")

    spotlight_search(make_env(runner=runner, find_mdfind=lambda: "/usr/bin/mdfind"))

    assert runner.calls[0][0][1:3] == ["-onlyin", "/Users/someone"]


def test_spotlight_candidate_folders_are_capped() -> None:
    hits = "\n".join(f"/v/Voice Memos {i}/x.m4a" for i in range(probe.MAX_SPOTLIGHT_FOLDERS + 10))

    result = spotlight_search(spotlight_env(Runner("", hits)))

    assert len(result.folders) == probe.MAX_SPOTLIGHT_FOLDERS


def test_spotlight_output_lines_are_capped() -> None:
    output = "\n" * probe.MAX_SPOTLIGHT_HITS + "/v/Voice Memos/x.m4a\n"

    result = spotlight_search(spotlight_env(Runner("", output)))

    assert result.folders == ()


def test_spotlight_timeout_keeps_what_was_found() -> None:
    timeout = subprocess.TimeoutExpired(["mdfind"], 10)

    result = spotlight_search(spotlight_env(Runner(DB_HIT, timeout)))

    assert result.status is SpotlightStatus.TIMEOUT
    assert result.folders == (Path(DB_HIT).parent,)
    assert "longer than" in (result.detail or "")


@pytest.mark.parametrize(
    "error",
    [OSError("boom"), subprocess.CalledProcessError(1, "mdfind")],
)
def test_spotlight_failure_is_an_error_status(error: Exception) -> None:
    result = spotlight_search(spotlight_env(Runner(error)))

    assert result.status is SpotlightStatus.ERROR
    assert result.detail


def test_spotlight_with_default_env_and_no_mdfind_does_not_raise() -> None:
    assert spotlight_search().status is SpotlightStatus.ABSENT


# Real subprocess and OS helpers


def test_run_command_returns_stdout() -> None:
    assert run_command([sys.executable, "-c", "print('hi')"], 10) == "hi\n"


def test_run_command_raises_on_failure() -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_command([sys.executable, "-c", "import sys; sys.exit(3)"], 10)


def test_run_command_times_out() -> None:
    with pytest.raises(subprocess.TimeoutExpired):
        run_command([sys.executable, "-c", "import time; time.sleep(5)"], 0.2)


def test_locate_mdfind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probe.os, "access", lambda path, _mode: path == probe.MDFIND_PATH)
    assert real_locate_mdfind() == probe.MDFIND_PATH

    monkeypatch.setattr(probe.os, "access", lambda _path, _mode: False)
    assert real_locate_mdfind() is None


class Unresolvable:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def resolve(self) -> Path:
        raise self.error


def test_resolve_path(tmp_path: Path) -> None:
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)

    assert resolve_path(link) == tmp_path.resolve()


@pytest.mark.parametrize("error", [OSError("denied"), RuntimeError("Symlink loop")])
def test_resolve_path_returns_the_input_on_failure(error: Exception) -> None:
    thing = cast(Path, Unresolvable(error))

    assert resolve_path(thing) is thing


# Plain-words time


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        (stamp(20, 9, 5), "today 9:05 am"),
        (stamp(20, 0, 30), "today 12:30 am"),
        (stamp(20, 12, 0), "today 12:00 pm"),
        (stamp(19, 16, 12), "yesterday 4:12 pm"),
        (stamp(3, 21, 45), "Sat 3 Oct 9:45 pm"),
        (stamp(3, 21, 45, month=10, year=2025), "Fri 3 Oct 2025 9:45 pm"),
    ],
)
def test_describe_time(timestamp: float, expected: str) -> None:
    assert describe_time(timestamp, NOW, UTC) == expected


def test_describe_time_uses_the_local_zone_by_default() -> None:
    assert describe_time(NOW, NOW).startswith("today ")


# Freshness


def test_freshness_stale_gives_icloud_steps() -> None:
    result = check_freshness(NOW - 10.5 * DAY, NOW, 7)

    assert result.stale
    assert "10 days old" in result.message
    assert "more than 7 days" in result.message
    assert any("iCloud" in step for step in result.steps)
    assert any("iPhone" in step for step in result.steps)


def test_freshness_singular_day() -> None:
    result = check_freshness(NOW - 1.5 * DAY, NOW, 1)

    assert result.stale
    assert "1 day old" in result.message


def test_freshness_recent_is_not_stale() -> None:
    result = check_freshness(NOW - 2 * DAY, NOW, 7)

    assert not result.stale
    assert result.steps == ()


def test_freshness_future_time_is_not_stale() -> None:
    assert not check_freshness(NOW + 5 * DAY, NOW, 7).stale


# Full Disk Access


def test_full_disk_access_help_names_the_resolved_interpreter() -> None:
    help_ = full_disk_access_help()

    assert help_.url == "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
    assert help_.interpreter == str(Path(sys.executable).resolve())
    assert help_.needed is True
    assert any(help_.interpreter in step for step in help_.steps)
    assert any(help_.url in step for step in help_.steps)
    assert "daemon install" in help_.launchd_note


def test_full_disk_access_help_resolves_through_the_given_env() -> None:
    env = make_env(resolve=lambda _p: Path("/opt/python/bin/python3.12"))

    help_ = full_disk_access_help(needed=False, executable="/venv/bin/python", env=env)

    assert help_.interpreter == "/opt/python/bin/python3.12"
    assert help_.needed is False


# run_probe


def no_spotlight_runner(_args: Any, _timeout: float) -> str:
    raise AssertionError("Spotlight must not run")


def test_a_readable_known_folder_is_chosen_and_spotlight_is_skipped(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", ["a.m4a", "b.m4a"])

    report = run_probe([folder], env=make_env(runner=no_spotlight_runner))

    assert report.chosen is not None
    assert report.chosen.path == folder
    assert report.summary == "Found 2 recordings, newest from yesterday 4:12 pm"
    assert report.ambiguous is False
    assert report.ambiguity is None
    assert report.alternatives == ()
    assert report.spotlight.status is SpotlightStatus.SKIPPED
    assert report.freshness is not None
    assert not report.freshness.stale
    assert report.full_disk_access.needed is False
    assert report.blocked is False


def test_a_single_recording_is_singular(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", ["a.m4a"])

    assert run_probe([folder], env=make_env()).summary.startswith("Found 1 recording,")


def test_the_folder_with_the_most_recordings_wins_and_ambiguity_is_flagged(
    tmp_path: Path,
) -> None:
    big = make_folder(tmp_path / "big", ["a.m4a", "b.m4a", "c.m4a"])
    small = make_folder(tmp_path / "small", ["d.m4a"])
    alias = tmp_path / "alias"
    alias.symlink_to(big, target_is_directory=True)

    report = run_probe([small, alias, big], env=make_env())

    assert report.chosen is not None
    assert report.chosen.memo_count == 3
    assert [p.path for p in report.alternatives] == [small]
    assert report.ambiguous is True
    assert report.ambiguity is not None
    assert "2 folders look plausible" in report.ambiguity
    assert "3 recordings" in report.ambiguity
    assert str(small) in report.ambiguity


def test_a_blocked_folder_is_reported_and_asks_for_full_disk_access(tmp_path: Path) -> None:
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    env = make_env(lister=blocking_lister(blocked), find_mdfind=lambda: None)

    report = run_probe([blocked, tmp_path / "missing"], env=env)

    assert report.chosen is None
    assert report.blocked is True
    assert "Full Disk Access" in report.summary
    assert report.full_disk_access.needed is True
    assert report.freshness is None
    assert report.spotlight.status is SpotlightStatus.ABSENT
    assert [p.state for p in report.known] == [PathState.BLOCKED, PathState.MISSING]


def test_a_readable_folder_beats_a_blocked_one(tmp_path: Path) -> None:
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    good = make_folder(tmp_path / "good", ["a.m4a"])

    report = run_probe([blocked, good], env=make_env(lister=blocking_lister(blocked)))

    assert report.chosen is not None
    assert report.chosen.path == good
    assert report.blocked is True
    assert report.full_disk_access.needed is True
    assert report.ambiguous is False


def test_an_empty_folder_is_explained(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    report = run_probe([empty, tmp_path / "missing"], env=make_env())

    assert report.chosen is None
    assert report.summary == "Found a Voice Memos folder, but it holds no recordings yet."


def test_nothing_found_is_explained(tmp_path: Path) -> None:
    report = run_probe([tmp_path / "a", tmp_path / "b"], env=make_env())

    assert report.chosen is None
    assert report.summary == "No Voice Memos folder was found in the usual places."
    assert report.blocked is False
    assert report.full_disk_access.needed is False


def test_spotlight_is_the_fallback_when_no_known_folder_is_readable(tmp_path: Path) -> None:
    known_missing = tmp_path / "Recordings"
    found = make_folder(tmp_path / "Voice Memos", ["a.m4a", "b.m4a"])
    runner = Runner(
        f"{known_missing}/CloudRecordings.db\n",
        f"{found}/a.m4a\n{found}/b.m4a\n",
    )

    report = run_probe([known_missing], env=spotlight_env(runner))

    assert report.spotlight.status is SpotlightStatus.OK
    assert [p.path for p in report.found] == [found]
    assert report.found[0].source == "spotlight"
    assert report.chosen is not None
    assert report.chosen.path == found
    assert report.chosen.source == "spotlight"


def test_spotlight_candidates_are_ranked_by_count_then_newest(tmp_path: Path) -> None:
    few = make_folder(tmp_path / "Voice Memos A", ["a.m4a"])
    many = make_folder(tmp_path / "Voice Memos B", ["a.m4a", "b.m4a", "c.m4a"])
    runner = Runner("", f"{few}/a.m4a\n{many}/a.m4a\n")

    report = run_probe([], env=spotlight_env(runner))

    assert report.chosen is not None
    assert report.chosen.path == many
    assert report.ambiguous is True


def test_a_blocked_spotlight_folder_counts_as_blocked(tmp_path: Path) -> None:
    found = tmp_path / "Voice Memos"
    found.mkdir()
    runner = Runner("", f"{found}/a.m4a\n")

    report = run_probe([], env=spotlight_env(runner, lister=blocking_lister(found)))

    assert report.chosen is None
    assert report.blocked is True
    assert "Full Disk Access" in report.summary


def test_spotlight_can_be_turned_off(tmp_path: Path) -> None:
    report = run_probe([tmp_path / "a"], spotlight=False, env=make_env(runner=no_spotlight_runner))

    assert report.spotlight == SpotlightResult(SpotlightStatus.SKIPPED, detail="turned off")
    assert report.chosen is None


def test_default_paths_come_from_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = make_folder(tmp_path / "Recordings", ["a.m4a"])
    monkeypatch.setattr(discovery, "VOICE_MEMOS_PATHS", (folder,))

    report = run_probe(env=make_env())

    assert report.chosen is not None
    assert report.chosen.path == folder


def test_a_truncated_count_is_a_lower_bound(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", [f"{i}.m4a" for i in range(5)])

    report = run_probe([folder], env=make_env(max_entries=2))

    assert report.summary.startswith("Found at least 2 recordings")


def test_old_recordings_trigger_the_sync_steps(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", ["a.m4a"], NOW - 30 * DAY)

    report = run_probe([folder], stale_days=7, env=make_env())

    assert report.freshness is not None
    assert report.freshness.stale
    assert "30 days old" in report.freshness.message
    assert report.freshness.steps


def test_the_stale_threshold_is_configurable(tmp_path: Path) -> None:
    folder = make_folder(tmp_path / "Recordings", ["a.m4a"], NOW - 30 * DAY)

    report = run_probe([folder], stale_days=60, env=make_env())

    assert report.freshness is not None
    assert not report.freshness.stale


def test_a_folder_with_no_known_times_has_no_freshness_or_newest(tmp_path: Path) -> None:
    def lister(_path: Path, _limit: int) -> tuple[list[Entry], bool]:
        return [Entry("a.m4a", True, None)], False

    report = run_probe([tmp_path], env=make_env(lister=lister))

    assert report.summary == "Found 1 recording"
    assert report.freshness is None


def test_the_report_serialises_to_json(tmp_path: Path) -> None:
    big = make_folder(tmp_path / "big", ["a.m4a", "b.m4a"])
    small = make_folder(tmp_path / "small", ["c.m4a"])
    missing = tmp_path / "missing"

    data = json.loads(json.dumps(run_probe([big, small, missing], env=make_env()).to_dict()))

    assert data["chosen"]["path"] == str(big)
    assert data["chosen"]["memo_count"] == 2
    assert data["chosen"]["newest"] == "2026-10-19T16:12:00+00:00"
    assert data["chosen"]["newest_text"] == "yesterday 4:12 pm"
    assert data["summary"] == "Found 2 recordings, newest from yesterday 4:12 pm"
    assert data["ambiguous"] is True
    assert [p["path"] for p in data["alternatives"]] == [str(small)]
    assert [p["state"] for p in data["known"]] == ["readable", "readable", "missing"]
    assert data["spotlight"]["status"] == "skipped"
    assert data["found"] == []
    assert data["freshness"]["stale"] is False
    assert data["full_disk_access"]["needed"] is False
    assert data["full_disk_access"]["url"].startswith("x-apple.systempreferences:")


def test_a_report_with_nothing_chosen_serialises(tmp_path: Path) -> None:
    data = run_probe([tmp_path / "missing"], env=make_env()).to_dict()

    assert data["chosen"] is None
    assert data["freshness"] is None
    assert data["known"][0]["newest"] is None
    assert json.dumps(data)
