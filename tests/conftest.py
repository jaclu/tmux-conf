"""
Test module
"""

import sys

import pytest


@pytest.fixture
def capture_stdout(monkeypatch):
    buffer = {"stdout": "", "write_calls": 0}

    def fake_write(s):
        buffer["stdout"] += s
        buffer["write_calls"] += 1

    monkeypatch.setattr(sys.stdout, "write", fake_write)
    return buffer


@pytest.fixture
def xdg_config_home(monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("XDG_CONFIG_HOME", "/tmp/foo/xdg")  # nosec
