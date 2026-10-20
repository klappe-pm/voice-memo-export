"""Guard against syntax that only parses on Python 3.12 or newer."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "vmea"


@pytest.mark.parametrize("path", sorted(SRC.rglob("*.py")), ids=lambda p: p.name)
def test_no_backslash_in_fstring_expression(path: Path) -> None:
    """A backslash inside an f-string expression is a syntax error on 3.11."""
    source = path.read_text(encoding="utf-8")
    offenders = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FormattedValue):
            segment = ast.get_source_segment(source, node.value) or ""
            if "\\" in segment:
                offenders.append((node.lineno, segment))
    assert offenders == []
