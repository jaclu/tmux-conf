# import pytest

import os
from pathlib import Path
from stat import S_IREAD, S_IWRITE

from src.tmux_conf import utils

from .common_vars import CONF_FILE


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


def test_utils_parse_clear_plugins():
    args = utils.parse_cmdline(["-c"])
    assert args.clear_plugins is True
    args = utils.parse_cmdline(["--clear_plugins"])
    assert args.clear_plugins is True


def test_utils_parse_replace():
    args = utils.parse_cmdline(["-r"])
    assert args.replace is True
    args = utils.parse_cmdline(["--replace"])
    assert args.replace is True


def test_utils_parse_plugins_display():
    for i in (1, 2, 3):
        args = utils.parse_cmdline(["-p", f"{i}"])
        assert args.plugins_display == i
        args = utils.parse_cmdline(["--plugins_display", f"{i}"])
        assert args.plugins_display == i

    for i in (0, 4):
        # test invalid plugin_display param
        r = False
        try:
            args = utils.parse_cmdline(["-p", f"{i}"])
        except SystemExit:
            r = True
        assert r == True

        r = False
        try:
            args = utils.parse_cmdline(["--plugins_display", f"{i}"])
        except SystemExit:
            r = True
        assert r == True


def test_utils_parse_tmux_bin():
    dummy_bin = "foo"
    args = utils.parse_cmdline(["-t", dummy_bin])
    assert args.tmux_bin == dummy_bin
    args = utils.parse_cmdline(["--tmux_bin", dummy_bin])
    assert args.tmux_bin == dummy_bin


def test_utils_parse_forced_version():
    args = utils.parse_cmdline(["-V", "2.4"])
    assert args.forced_version == "2.4"
    args = utils.parse_cmdline(["--forced-version", "2.4"])
    assert args.forced_version == "2.4"


def test_utils_parse_conf_file():
    args = utils.parse_cmdline([CONF_FILE])
    assert args.conf_file == CONF_FILE


def test_utils_run_shell():
    hw = "Hello world"
    assert utils.run_shell(f"echo {hw}") == hw


def test_utils_tilde_home_dir():
    tilde_name = "~/tmp"
    full_path = utils.expanduser_plus(tilde_name)
    assert utils.tilde_home_dir(full_path) == tilde_name


def test_utils_conf_file_useable_empty():
    r = False
    try:
        utils.verify_conf_file_usable("")
    except SyntaxError:
        # expected result, should be rissen for empty conf file,  all is good
        r = True
    assert r is True


def test_utils_conf_file_useable_relative():
    #
    #  Test that if no path is given, it is expanded to cwd
    #
    conf_relative = "local_conf.conf"
    full_path_cf = utils.verify_conf_file_usable(conf_relative)
    # get where this is run
    path_test = Path(os.path.dirname(os.path.realpath(__file__)))
    # get parent dir, assumed to be proj dir
    path_proj = path_test.parent.absolute()
    assert full_path_cf == f"{path_proj}/{conf_relative}"


def test_utils_conf_file_useable_readonly_fs():
    conf_ro_fs = "/root/foo/dummy.conf"
    r = False
    try:
        utils.verify_conf_file_usable(conf_ro_fs)
    except OSError:
        r = True
    assert r is True


def test_utils_conf_file_useable_readonly_file():
    conf_ro_file = "/tmp/foo123.conf"
    Path(conf_ro_file).touch()
    os.chmod(conf_ro_file, S_IREAD)
    r = False
    try:
        utils.verify_conf_file_usable(conf_ro_file)
    except IOError:
        # expected result, should be rissen for read only fs,  all is good
        r = True
    os.chmod(conf_ro_file, S_IWRITE)
    os.remove(conf_ro_file)
    assert r is True
