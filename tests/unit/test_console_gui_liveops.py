import pytest

from Artefact.console import interactive_mode
from Artefact.gui import launch_gui
from Artefact.modules import liveops


def test_interactive_console_help_command_and_exit(monkeypatch, capsys):
    commands = iter(["help", "--version", "quit"])
    assert interactive_mode(lambda prompt: next(commands)) == 0
    output = capsys.readouterr().out
    assert "interactive mode" in output
    assert "ARTEFACT 1.0.0" in output


def test_gui_has_actionable_optional_dependency_error():
    try:
        import PySide6  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match="PySide6"):
            launch_gui()


def test_liveops_processes_connections_and_validation(monkeypatch):
    class Process:
        info = {"pid": 1, "name": "init"}

    class Connection:
        fd, family, type, laddr, raddr, status, pid = 1, 2, 1, ("127.0.0.1", 1), (), "LISTEN", 1

    class Psutil:
        class NoSuchProcess(Exception):
            pass
        class AccessDenied(Exception):
            pass

        @staticmethod
        def process_iter(fields):
            return [Process()]

        @staticmethod
        def net_connections(kind):
            return [Connection()]

    monkeypatch.setattr(liveops, "_psutil", lambda: Psutil)
    assert liveops.list_processes()[0]["pid"] == 1
    assert liveops.list_connections()[0]["status"] == "LISTEN"
    assert set(liveops.collect(["processes", "network"])) == {"processes", "network"}
    with pytest.raises(ValueError, match="Unsupported"):
        liveops.collect(["registry"])
