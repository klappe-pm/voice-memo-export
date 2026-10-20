"""Command level tests for the VMEA CLI, with filesystem and subprocess isolated."""

import os
import plistlib
import subprocess
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from vmea import cli
from vmea.cli import app
from vmea.config import VMEAConfig

runner = CliRunner()


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point HOME at a temporary directory so config and logs never touch the real one."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home


def write_config(home: Path, source: Path | None = None) -> VMEAConfig:
    config = VMEAConfig(output_folder=home / "notes", source_path_override=source)
    config_path = home / ".config" / "vmea" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(cli.render_config_content(config))
    return config


def completed(
    returncode: int = 0, stdout: str | bytes = "", stderr: str | bytes = ""
) -> subprocess.CompletedProcess[Any]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class RunRecorder:
    """Stand in for subprocess.run and remember every call."""

    def __init__(self, result: subprocess.CompletedProcess[Any] | Exception) -> None:
        self.result = result
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[Any]:
        self.calls.append(list(args))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


# shortcut-setup


def test_shortcut_setup_is_registered() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "shortcut-setup" in result.output


def test_shortcut_installed_true_when_listed(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = RunRecorder(completed(stdout="Other\nVMEA Open\n"))
    monkeypatch.setattr(cli.subprocess, "run", recorder)

    assert cli.shortcut_installed() is True
    assert recorder.calls == [["shortcuts", "list"]]


@pytest.mark.parametrize(
    "result",
    [
        completed(stdout="Other\n"),
        completed(returncode=1, stdout="VMEA Open\n"),
        FileNotFoundError("shortcuts"),
        subprocess.TimeoutExpired(cmd="shortcuts", timeout=10),
    ],
)
def test_shortcut_installed_false_otherwise(
    monkeypatch: pytest.MonkeyPatch, result: subprocess.CompletedProcess[Any] | Exception
) -> None:
    monkeypatch.setattr(cli.subprocess, "run", RunRecorder(result))

    assert cli.shortcut_installed() is False


def test_shortcut_setup_off_macos_prints_steps_without_checking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = RunRecorder(completed())
    monkeypatch.setattr(cli.subprocess, "run", recorder)
    monkeypatch.setattr(cli.sys, "platform", "linux")

    result = runner.invoke(app, ["shortcut-setup"])

    assert result.exit_code == 0
    assert "Run Shell Script" in result.output
    assert recorder.calls == []


def test_shortcut_setup_on_macos_reports_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = RunRecorder(completed(stdout="VMEA Open\n"))
    monkeypatch.setattr(cli.subprocess, "run", recorder)
    monkeypatch.setattr(cli.sys, "platform", "darwin")

    result = runner.invoke(app, ["shortcut-setup"])

    assert result.exit_code == 0
    assert "installed" in result.output
    assert recorder.calls == [["shortcuts", "list"]]


def test_shortcut_setup_on_macos_guides_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli.subprocess, "run", RunRecorder(completed(stdout="Other\n")))
    monkeypatch.setattr(cli.sys, "platform", "darwin")

    result = runner.invoke(app, ["shortcut-setup"])

    assert result.exit_code == 1
    assert "Run Shell Script" in result.output
    assert "VMEA Open" in result.output


def test_setup_vmea_shortcut_names_the_command(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.subprocess, "run", RunRecorder(completed(stdout="")))
    monkeypatch.setattr(cli.typer, "confirm", lambda *_a, **_k: True)

    cli.setup_vmea_shortcut()

    assert "vmea shortcut-setup" in capsys.readouterr().out


def test_setup_vmea_shortcut_returns_true_when_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli.subprocess, "run", RunRecorder(completed(stdout="VMEA Open\n")))

    assert cli.setup_vmea_shortcut() is True


def test_setup_vmea_shortcut_skip(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli.subprocess, "run", RunRecorder(completed(stdout="")))
    monkeypatch.setattr(cli.typer, "confirm", lambda *_a, **_k: False)

    assert cli.setup_vmea_shortcut() is False
    assert "Skipping shortcut setup" in capsys.readouterr().out


# daemon


def test_build_launchd_plist_escapes_special_characters(tmp_path: Path) -> None:
    home = tmp_path / "a&b<c>"
    logs = home / ".local" / "share" / "vmea"

    data = cli.build_launchd_plist("/opt/py&thon/bin/python", logs, home)

    parsed = plistlib.loads(data)
    assert parsed["Label"] == "dev.vmea.agent"
    assert parsed["ProgramArguments"] == ["/opt/py&thon/bin/python", "-m", "vmea", "watch"]
    assert parsed["WorkingDirectory"] == str(home)
    assert parsed["StandardOutPath"] == f"{logs}/vmea-stdout.log"
    assert b"a&amp;b&lt;c&gt;" in data


def test_daemon_install_bootstraps_and_writes_valid_plist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_home = tmp_path / "me&you<x>"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    plist_path = fake_home / "Library" / "LaunchAgents" / "dev.vmea.agent.plist"
    monkeypatch.setattr(cli, "LAUNCHD_PLIST_PATH", plist_path)
    recorder = RunRecorder(completed())
    monkeypatch.setattr(cli.subprocess, "run", recorder)

    result = runner.invoke(app, ["daemon", "install"])

    assert result.exit_code == 0
    assert recorder.calls == [["launchctl", "bootstrap", f"gui/{os.getuid()}", str(plist_path)]]
    parsed = plistlib.loads(plist_path.read_bytes())
    assert parsed["WorkingDirectory"] == str(fake_home)


def test_daemon_install_reports_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(cli, "LAUNCHD_PLIST_PATH", tmp_path / "dev.vmea.agent.plist")
    monkeypatch.setattr(cli.subprocess, "run", RunRecorder(completed(5, stderr=b"nope")))

    result = runner.invoke(app, ["daemon", "install"])

    assert result.exit_code == 1
    assert "nope" in result.output


def test_daemon_install_refuses_when_already_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plist_path = tmp_path / "dev.vmea.agent.plist"
    plist_path.write_bytes(b"x")
    monkeypatch.setattr(cli, "LAUNCHD_PLIST_PATH", plist_path)
    recorder = RunRecorder(completed())
    monkeypatch.setattr(cli.subprocess, "run", recorder)

    result = runner.invoke(app, ["daemon", "install"])

    assert result.exit_code == 1
    assert recorder.calls == []


def test_daemon_uninstall_boots_out_and_removes_plist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plist_path = tmp_path / "dev.vmea.agent.plist"
    plist_path.write_bytes(b"x")
    monkeypatch.setattr(cli, "LAUNCHD_PLIST_PATH", plist_path)
    recorder = RunRecorder(completed())
    monkeypatch.setattr(cli.subprocess, "run", recorder)

    result = runner.invoke(app, ["daemon", "uninstall"])

    assert result.exit_code == 0
    assert recorder.calls == [["launchctl", "bootout", f"gui/{os.getuid()}", str(plist_path)]]
    assert not plist_path.exists()


def test_daemon_uninstall_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "LAUNCHD_PLIST_PATH", tmp_path / "missing.plist")

    result = runner.invoke(app, ["daemon", "uninstall"])

    assert result.exit_code == 0
    assert "not installed" in result.output


def test_daemon_status_variants(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plist_path = tmp_path / "dev.vmea.agent.plist"
    monkeypatch.setattr(cli, "LAUNCHD_PLIST_PATH", plist_path)
    assert "not installed" in runner.invoke(app, ["daemon", "status"]).output

    plist_path.write_bytes(b"x")
    monkeypatch.setattr(cli.subprocess, "run", RunRecorder(completed(stdout="123\t0\tdev.vmea.agent")))
    running = runner.invoke(app, ["daemon", "status"])
    assert "running" in running.output

    monkeypatch.setattr(cli.subprocess, "run", RunRecorder(completed(returncode=113)))
    stopped = runner.invoke(app, ["daemon", "status"])
    assert "not running" in stopped.output


# config, doctor, list


@pytest.mark.usefixtures("home")
def test_config_without_file_exits() -> None:
    result = runner.invoke(app, ["config"])

    assert result.exit_code == 1
    assert "No config found" in result.output


def test_config_shows_values(home: Path) -> None:
    source = home / "memos"
    source.mkdir()
    write_config(home, source)

    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0
    assert "Voice Memos app" in result.output
    assert "(override)" in result.output


@pytest.mark.usefixtures("home")
def test_doctor_without_config_reports_issues() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "Config not found" in result.output


def test_doctor_passes_with_config_and_source(home: Path) -> None:
    source = home / "memos"
    source.mkdir()
    (source / "20240101 120000-ABC.m4a").write_bytes(b"")
    write_config(home, source)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Found 1 memo(s)" in result.output
    assert "All checks passed" in result.output


@pytest.mark.usefixtures("home")
def test_list_without_source_exits() -> None:
    result = runner.invoke(app, ["list"])

    assert result.exit_code == 1
    assert "not found" in result.output


def test_list_shows_memos(home: Path) -> None:
    source = home / "memos"
    source.mkdir()
    (source / "20240101 120000-ABC.m4a").write_bytes(b"")
    write_config(home, source)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "Voice Memos (1)" in result.output


def test_list_with_no_memos(home: Path) -> None:
    source = home / "memos"
    source.mkdir()
    write_config(home, source)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "No voice memos found" in result.output


# init


def test_init_writes_config_and_prints_pipeline(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = home / "notes"
    monkeypatch.setattr(cli.shutil, "which", lambda _name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(cli, "choose_folder", lambda _prompt: output)
    monkeypatch.setattr(cli, "find_source_path", lambda *_a, **_k: None)
    monkeypatch.setattr(cli, "is_ollama_running", lambda _host: True)
    monkeypatch.setattr(cli, "prompt_ollama_models", lambda **_k: ["m1", "m2", "m3"])
    monkeypatch.setattr(cli, "setup_vmea_shortcut", lambda: False)

    result = runner.invoke(app, ["init"], input="\n\n")

    assert result.exit_code == 0, result.output
    assert "Whisper → m1 → m2 → m3" in result.output
    config_text = (home / ".config" / "vmea" / "config.toml").read_text()
    assert 'audio_export_mode = "app-link"' in config_text
