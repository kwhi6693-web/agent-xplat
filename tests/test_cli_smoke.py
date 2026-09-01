from agent_xplat import __version__
from agent_xplat.cli import main


def test_package_exposes_version():
    assert __version__ == "1.0.0"


def test_cli_help_returns_zero(capsys):
    assert main(["--help"]) == 0
    assert "Cross-OS Runtime Portability" in capsys.readouterr().out
