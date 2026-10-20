"""Command level tests for `vmea probe` and the probe section of `vmea doctor`."""

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from vmea import cli, probe
from vmea.cli import app, describe_probe
from vmea.config import VMEAConfig
from vmea.probe import PathProbe, PathState

runner = CliRunner()

GROUP = "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home


def fill(folder: Path, count: int, age_days: float = 0) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        file = folder / f"memo-{i}.m4a"
        file.write_bytes(b"audio")
        if age_days:
            old = file.stat().st_mtime - age_days * 86_400
            os.utime(file, (old, old))
    return folder


def write_config(home: Path, source: Path) -> None:
    config = VMEAConfig(output_folder=home / "notes", source_path_override=source)
    path = home / ".config" / "vmea" / "config.toml"
    path.parent.mkdir(parents=True)
    path.write_text(cli.render_config_content(config))


def block(monkeypatch: pytest.MonkeyPatch, blocked: Path) -> None:
    real = os.scandir

    def fake(path: Any) -> Any:
        if Path(path) == blocked:
            raise PermissionError(1, "Operation not permitted")
        return real(path)

    monkeypatch.setattr(probe.os, "scandir", fake)


# vmea probe


def test_probe_is_registered() -> None:
    result = runner.invoke(app, ["--help"])

    assert "probe" in result.output


def test_probe_json_for_a_readable_folder(home: Path) -> None:
    fill(home / GROUP, 2)

    result = runner.invoke(app, ["probe", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["chosen"]["path"] == str(home / GROUP)
    assert data["chosen"]["memo_count"] == 2
    assert data["chosen"]["state"] == "readable"
    assert data["spotlight"]["status"] == "skipped"
    assert len(data["known"]) == len(cli.VOICE_MEMOS_PATHS)
    assert data["summary"].startswith("Found 2 recordings, newest from today")


def test_probe_json_exits_1_when_nothing_is_readable(home: Path) -> None:
    assert home.exists()

    result = runner.invoke(app, ["probe", "--json"])

    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["chosen"] is None
    assert data["spotlight"]["status"] == "absent"
    assert {p["state"] for p in data["known"]} == {"missing"}


def test_probe_no_spotlight_flag(home: Path) -> None:
    assert home.exists()

    result = runner.invoke(app, ["probe", "--json", "--no-spotlight"])

    assert json.loads(result.output)["spotlight"]["status"] == "skipped"


def test_probe_prints_a_plain_language_result(home: Path) -> None:
    fill(home / GROUP, 2)

    result = runner.invoke(app, ["probe"])

    assert result.exit_code == 0, result.output
    assert "Voice Memos folders checked" in result.output
    assert "readable" in result.output
    assert "Found 2 recordings, newest from today" in result.output
    assert "Using:" in result.output


def test_probe_explains_when_nothing_is_found(home: Path) -> None:
    assert home.exists()

    result = runner.invoke(app, ["probe"])

    assert result.exit_code == 1
    assert "No Voice Memos folder was found" in result.output
    assert "Spotlight search absent" in result.output
    assert "missing" in result.output


def test_probe_blocked_folder_shows_the_full_disk_access_fix(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = fill(home / GROUP, 2)
    block(monkeypatch, folder)

    result = runner.invoke(app, ["probe"])

    assert result.exit_code == 1
    assert "blocked" in result.output
    assert "Operation not permitted" in result.output
    assert "Full Disk Access is needed" in result.output
    assert "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles" in result.output
    assert str(Path(sys.executable).resolve()) in result.output
    assert "Command Shift G" in result.output
    assert "daemon install" in result.output


def test_probe_warns_when_the_newest_recording_is_old(home: Path) -> None:
    fill(home / GROUP, 1, age_days=30)

    result = runner.invoke(app, ["probe"])

    assert result.exit_code == 0
    assert "may not be syncing" in result.output
    assert "Show All" in result.output


def test_probe_stale_days_option(home: Path) -> None:
    fill(home / GROUP, 1, age_days=30)

    result = runner.invoke(app, ["probe", "--stale-days", "60"])

    assert "may not be syncing" not in result.output


def test_probe_flags_ambiguity(home: Path) -> None:
    fill(home / GROUP, 3)
    fill(home / "Library/Mobile Documents/com~apple~VoiceMemos/Recordings", 1)

    result = runner.invoke(app, ["probe"])

    assert result.exit_code == 0
    assert "2 folders look plausible" in result.output


def test_probe_honours_the_configured_source_override(home: Path) -> None:
    custom = fill(home / "custom", 5)
    fill(home / GROUP, 1)
    write_config(home, custom)

    result = runner.invoke(app, ["probe", "--json"])

    data = json.loads(result.output)
    assert data["known"][0]["path"] == str(custom)
    assert data["chosen"]["path"] == str(custom)


def test_probe_when_spotlight_finds_folders(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    found = fill(home / "Voice Memos", 2)
    real_run_probe = cli.run_probe

    def fake_run_probe(paths: Any = None, **kwargs: Any) -> Any:
        env = probe.ProbeEnv(
            runner=lambda _args, _timeout: f"{found}/memo-0.m4a\n{found}/memo-1.m4a\n",
            find_mdfind=lambda: "/usr/bin/mdfind",
        )
        return real_run_probe(paths, env=env, **kwargs)

    monkeypatch.setattr(cli, "run_probe", fake_run_probe)

    result = runner.invoke(app, ["probe"])

    assert result.exit_code == 0, result.output
    assert "Spotlight suggested 1 other folder(s)" in result.output
    assert "Found 2 recordings" in result.output


# vmea doctor


def test_doctor_shows_states_and_the_chosen_folder(home: Path) -> None:
    source = fill(home / "memos", 1)
    write_config(home, source)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
    assert "Voice Memos folders checked" in result.output
    assert "Found 1 recording, newest from today" in result.output
    assert "Using:" in result.output
    assert "missing" in result.output
    assert "All checks passed" in result.output


def test_doctor_lists_every_known_path_when_nothing_is_found(home: Path) -> None:
    write_config(home, home / "gone")

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "Voice Memos folder not found" in result.output
    assert "To fix:" in result.output
    assert "Voice Memos folders checked" in result.output
    assert result.output.count("missing") >= len(cli.VOICE_MEMOS_PATHS)


def test_doctor_reports_a_blocked_folder_instead_of_crashing(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = fill(home / "memos", 2)
    write_config(home, source)
    block(monkeypatch, source)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "macOS will not let this program read that folder" in result.output
    assert "Full Disk Access is needed" in result.output
    assert "1 issue(s) found" in result.output


# describe_probe


def test_describe_probe() -> None:
    folder = Path("/x")

    readable = PathProbe(folder, PathState.READABLE, 5, 1.0, "yesterday 4:12 pm")
    truncated = PathProbe(folder, PathState.READABLE, 5, truncated=True)
    blocked = PathProbe(folder, PathState.BLOCKED, detail="Operation not permitted")

    assert describe_probe(readable) == "(5 recordings, newest yesterday 4:12 pm)"
    assert describe_probe(truncated) == "(5+ recordings)"
    assert describe_probe(blocked) == "(Operation not permitted)"
    assert describe_probe(PathProbe(folder, PathState.BLOCKED)) == ""
    assert describe_probe(PathProbe(folder, PathState.EMPTY)) == ""
    assert describe_probe(PathProbe(folder, PathState.MISSING)) == ""
