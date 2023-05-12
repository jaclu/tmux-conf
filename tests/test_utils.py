import os
import tempfile
from pathlib import Path
from stat import S_IREAD, S_IWRITE

import pytest
from src.tmux_conf import utils

from .utils_test import CONF_FILE


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("no bticks", False),
        ("bticks present ` ", True),
        ("double escaped btick \\` ", False),
    ],
)
def not_test_utils_btick(test_input, expected):
    assert utils.btick_unescaped(test_input) is expected


def not_test_utils_expanduser_plus():
    username = str(os.environ.get("USER"))
    tilde = utils.expanduser_plus("~")
    home = utils.expanduser_plus("$HOME")
    assert tilde == home
    assert home.find(username) > -1
    assert tilde.find(username) > -1


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("/etc/passwd", False),
        ("/bin/sh", True),
    ],
)
def not_test_utils_is_executable(test_input, expected):
    assert utils.is_executable(test_input) is expected


@pytest.mark.parametrize(
    "test_input",
    [
        ("-c"),
        ("--clear_plugins"),
    ],
)
def not_test_utils_parse_clear_plugins(test_input):
    args = utils.parse_cmdline([test_input])
    assert args.clear_plugins is True


def not_test_utils_parse_replace():
    args = utils.parse_cmdline(["-r"])
    assert args.replace is True
    args = utils.parse_cmdline(["--replace"])
    assert args.replace is True


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("", 0),
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 0),
    ],
)
def not_test_utils_parse_plugins_display(test_input, expected):
    if expected > 0:
        args = utils.parse_cmdline(["-p", f"{test_input}"])
        assert args.plugins_display == expected
        args = utils.parse_cmdline(["--plugins_display", f"{test_input}"])
        assert args.plugins_display == expected
    else:
        with pytest.raises(SystemExit):
            args = utils.parse_cmdline(["-p", f"{test_input}"])
        with pytest.raises(SystemExit):
            args = utils.parse_cmdline(["--plugins_display", f"{test_input}"])


def not_test_utils_parse_tmux_bin():
    dummy_bin = "foo"
    args = utils.parse_cmdline(["-t", dummy_bin])
    assert args.tmux_bin == dummy_bin
    args = utils.parse_cmdline(["--tmux_bin", dummy_bin])
    assert args.tmux_bin == dummy_bin


def not_test_utils_parse_forced_version():
    args = utils.parse_cmdline(["-V", "2.4"])
    assert args.forced_version == "2.4"
    args = utils.parse_cmdline(["--forced-version", "2.4"])
    assert args.forced_version == "2.4"


def not_test_utils_parse_conf_file():
    args = utils.parse_cmdline([CONF_FILE])
    assert args.conf_file == CONF_FILE


def not_test_utils_run_shell():
    hw = "Hello world"
    assert utils.run_shell(f"echo {hw}") == hw


def not_test_utils_tilde_home_dir():
    tilde_name = "~/tmp"
    full_path = utils.expanduser_plus(tilde_name)
    assert utils.tilde_home_dir(full_path) == tilde_name


def not_test_utils_not_tilde_home_dir():
    tmp_dir = tempfile.mkdtemp()
    assert utils.tilde_home_dir(tmp_dir) == tmp_dir


def not_test_utils_conf_file_useable_empty():
    with pytest.raises(SyntaxError):
        utils.verify_conf_file_usable("")


def not_test_utils_conf_file_useable_relative():
    #
    #  Test that if no path is given, it is expanded to cwd
    #
    conf_relative = "local_conf.conf"
    conf_file = os.path.join(os.getcwd(), conf_relative)
    generated_full_path_cf = utils.verify_conf_file_usable(conf_relative)
    assert generated_full_path_cf == conf_file


def not_test_utils_conf_file_useable_readonly_fs():
    conf_ro_fs = "/root/foo/dummy.conf"
    with pytest.raises(OSError):
        utils.verify_conf_file_usable(conf_ro_fs)


def not_test_utils_conf_file_useable_readonly_file():
    conf_ro_file = tempfile.NamedTemporaryFile()
    Path(conf_ro_file.name).touch()
    os.chmod(conf_ro_file.name, S_IREAD)
    with pytest.raises(IOError):
        utils.verify_conf_file_usable(conf_ro_file.name)
    os.chmod(conf_ro_file.name, S_IWRITE)
