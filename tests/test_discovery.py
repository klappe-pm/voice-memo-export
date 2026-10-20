"""Tests for VMEA discovery module."""

import os
from pathlib import Path
from typing import Any

import pytest

from vmea import discovery, probe
from vmea.discovery import MemoPair, diagnose_paths, discover_memos, find_source_path


@pytest.fixture
def known_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Point the known Voice Memos paths at two fixture folders."""
    paths = (tmp_path / "first", tmp_path / "second")
    monkeypatch.setattr(discovery, "VOICE_MEMOS_PATHS", paths)
    return paths


def fill(folder: Path, count: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (folder / f"memo-{i}.m4a").write_bytes(b"audio")


def block(monkeypatch: pytest.MonkeyPatch, blocked: Path) -> None:
    real = os.scandir

    def fake(path: Any) -> Any:
        if Path(path) == blocked:
            raise PermissionError(1, "Operation not permitted")
        return real(path)

    monkeypatch.setattr(probe.os, "scandir", fake)


def test_find_source_path_prefers_the_folder_with_most_recordings(
    known_paths: tuple[Path, Path],
) -> None:
    first, second = known_paths
    fill(first, 1)
    fill(second, 4)

    assert find_source_path() == second


def test_find_source_path_skips_a_blocked_folder_for_a_readable_one(
    known_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = known_paths
    fill(first, 9)
    fill(second, 1)
    block(monkeypatch, first)

    assert find_source_path() == second


def test_find_source_path_falls_back_to_a_blocked_folder_that_exists(
    known_paths: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    first, _second = known_paths
    fill(first, 2)
    block(monkeypatch, first)

    assert find_source_path() == first


def test_find_source_path_falls_back_to_the_first_existing_empty_folder(
    known_paths: tuple[Path, Path],
) -> None:
    _first, second = known_paths
    second.mkdir()

    assert find_source_path() == second


def test_find_source_path_none_when_nothing_exists(known_paths: tuple[Path, Path]) -> None:
    assert known_paths
    assert find_source_path() is None


def test_diagnose_paths_reports_existence_and_count(known_paths: tuple[Path, Path]) -> None:
    first, second = known_paths
    fill(first, 3)

    assert diagnose_paths() == [(first, True, 3), (second, False, 0)]


def test_find_source_path_with_override(temp_dir: Path) -> None:
    """Test that override path is used when provided."""
    recordings = temp_dir / "custom_recordings"
    recordings.mkdir()

    result = find_source_path(override=recordings)
    assert result == recordings


def test_find_source_path_override_not_exists(temp_dir: Path) -> None:
    """Test that None is returned for non-existent override path."""
    result = find_source_path(override=temp_dir / "nonexistent")
    assert result is None


def test_discover_memos_empty_dir(temp_dir: Path) -> None:
    """Test discovery in empty directory."""
    memos = list(discover_memos(temp_dir))
    assert memos == []


def test_discover_memos_with_audio_only(temp_dir: Path) -> None:
    """Test discovery of memo without composition folder."""
    audio_file = temp_dir / "memo-123.m4a"
    audio_file.write_bytes(b"fake audio")

    memos = list(discover_memos(temp_dir))

    assert len(memos) == 1
    assert memos[0].memo_id == "memo-123"
    assert memos[0].audio_path == audio_file
    assert memos[0].composition_path is None
    assert not memos[0].has_composition


def test_discover_memos_with_composition(mock_voice_memos_dir: Path) -> None:
    """Test discovery of memo with composition folder."""
    memos = list(discover_memos(mock_voice_memos_dir))

    assert len(memos) == 1
    memo = memos[0]
    assert memo.memo_id == "test-memo-001"
    assert memo.has_composition
    assert memo.composition_path is not None
    assert (memo.composition_path / "manifest.plist").exists()


def test_discover_memos_multiple(temp_dir: Path) -> None:
    """Test discovery of multiple memos."""
    for i in range(3):
        (temp_dir / f"memo-{i}.m4a").write_bytes(b"audio")

    memos = list(discover_memos(temp_dir))
    assert len(memos) == 3
    memo_ids = {m.memo_id for m in memos}
    assert memo_ids == {"memo-0", "memo-1", "memo-2"}


def test_memo_pair_properties() -> None:
    """Test MemoPair dataclass properties."""
    pair = MemoPair(
        audio_path=Path("/test/memo.m4a"),
        composition_path=None,
        memo_id="memo",
    )
    assert not pair.has_composition
