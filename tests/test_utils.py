# import pytest

import os

from src.tmux_conf import utils


def test_utils_btick():
    assert utils.btick_unescaped("no bticks") is not True
    assert utils.btick_unescaped("bticks present ` ") is True
    assert utils.btick_unescaped("double escaped btick \\` ") is not True


def test_utils_expanduser_plus():
    username = str(os.environ.get("USER"))
    tilde = utils.expanduser_plus("~")
    assert tilde.find(username) > -1
    home = utils.expanduser_plus("$HOME")
    assert home.find(username) > -1
    assert tilde == home


def test_utils_is_executable():
    assert utils.is_executable("/etc/passwd") is not True
    assert utils.is_executable("/bin/sh") is True


def test_utils_run_shell():
    hw = "Hello world"
    assert utils.run_shell(f"echo {hw}") == hw


def test_utils_tilde_home_dir():
    tilde_name = "~/tmp"
    full_path = utils.expanduser_plus(tilde_name)
    assert utils.tilde_home_dir(full_path) == tilde_name
