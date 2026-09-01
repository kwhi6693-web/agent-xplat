from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.engine import scan
from agent_xplat.reporting import render_terminal


ROOT = Path(__file__).parents[1]


def test_mixed_fixture_terminal_report_matches_snapshot():
    fixture = ROOT / "tests" / "fixtures" / "mixed"
    snapshot = ROOT / "tests" / "snapshots" / "mixed-terminal.txt"
    actual = render_terminal(scan(fixture, Config()), color=False)
    expected = snapshot.read_text(encoding="utf-8")
    assert actual == expected
