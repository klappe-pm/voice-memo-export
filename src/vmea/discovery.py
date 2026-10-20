"""VMEA Discovery – Find and enumerate Voice Memos on the system."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Known Voice Memos locations on macOS (checked in order of preference)
# Reference: Apple documentation and empirical testing across macOS versions
VOICE_MEMOS_PATHS = [
    # macOS Sonoma (14.x) / Sequoia (15.x) - Group Containers (most common current path)
    Path("~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"),
    # iCloud Drive sync staging folder (Mobile Documents)
    Path("~/Library/Mobile Documents/com~apple~VoiceMemos/Recordings"),
    # macOS Sonoma+ Containers path variant
    Path("~/Library/Containers/com.apple.VoiceMemos/Data/Library/Application Support/Recordings"),
    # macOS Ventura (13.x) and earlier
    Path("~/Library/Application Support/com.apple.voicememos/Recordings"),
    # Alternative Application Support path (case variant)
    Path("~/Library/Application Support/com.apple.VoiceMemos/Recordings"),
]


@dataclass
class MemoPair:
    """A paired Voice Memo: .m4a audio file + .composition metadata folder."""

    audio_path: Path
    composition_path: Path | None  # May not exist for older memos
    memo_id: str  # Derived from filename stem

    @property
    def has_composition(self) -> bool:
        """Check if composition metadata exists."""
        return self.composition_path is not None and self.composition_path.exists()


def find_source_path(override: Path | None = None) -> Path | None:
    """Find the Voice Memos source directory.

    Without an override, every known path is probed and the readable folder with the most
    recordings wins. If none is readable, the first path that exists is returned as before, so
    callers can still report a blocked or empty folder. Spotlight is not consulted here; use
    `vmea.probe.run_probe` for that.

    Args:
        override: Optional user-specified path.

    Returns:
        Path to Voice Memos directory, or None if not found.
    """
    if override:
        expanded = override.expanduser()
        if expanded.exists():
            return expanded
        return None

    # Imported here because vmea.probe reads VOICE_MEMOS_PATHS from this module.
    from vmea import probe

    env = probe.ProbeEnv()
    probes = [probe.probe_path(path, env) for path in VOICE_MEMOS_PATHS]
    ranked = probe.rank_readable(probes, env)
    if ranked:
        return ranked[0].path
    for item in probes:
        if item.state is not probe.PathState.MISSING:
            return item.path

    return None


def discover_memos(source_path: Path) -> Iterator[MemoPair]:
    """Discover all Voice Memos in the source directory.

    Yields MemoPair objects for each .m4a file found, paired with its
    .composition folder if it exists.

    Args:
        source_path: Path to Voice Memos directory.

    Yields:
        MemoPair for each discovered memo.
    """
    if not source_path.exists():
        return

    for audio_file in source_path.glob("*.m4a"):
        memo_id = audio_file.stem
        composition_path = source_path / f"{memo_id}.composition"

        yield MemoPair(
            audio_path=audio_file,
            composition_path=composition_path if composition_path.exists() else None,
            memo_id=memo_id,
        )


def diagnose_paths() -> list[tuple[Path, bool, int]]:
    """Check all known Voice Memos paths and report status.

    Kept for compatibility. `vmea.probe.run_probe` reports the richer four-state result.

    Returns:
        List of (path, exists, memo_count) tuples.
    """
    from vmea import probe

    env = probe.ProbeEnv()
    results = []
    for path in VOICE_MEMOS_PATHS:
        item = probe.probe_path(path, env)
        results.append((item.path, item.state is not probe.PathState.MISSING, item.memo_count))
    return results


def check_file_stability(path: Path, check_count: int = 3, interval: float = 2.0) -> bool:
    """Check if a file is stable (not being written to).

    Used to avoid processing partially-synced iCloud files.

    Args:
        path: Path to check.
        check_count: Number of stability checks.
        interval: Seconds between checks.

    Returns:
        True if file size remained constant across all checks.
    """
    import time

    if not path.exists():
        return False

    sizes: list[int] = []
    for _ in range(check_count):
        try:
            sizes.append(path.stat().st_size)
        except OSError:
            return False
        if len(sizes) < check_count:
            time.sleep(interval)

    return len(set(sizes)) == 1
