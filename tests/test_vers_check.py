import pytest

from src.tmux_conf.vers_check import VersionCheck


def test_vc_missing_subvers():
    with pytest.raises(IndexError):
        VersionCheck("3")


def test_vc_maj_not_int():
    with pytest.raises(ValueError):
        VersionCheck("a.b")


def test_vc_bad_suffix():
    with pytest.raises(ValueError):
        VersionCheck("3.b")


def test_vc_low():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck(3.2)
    assert vc.is_ok(3.1) is True  # noqa


# def test_tc_bin_bad_vers():
#     t = TmuxConfig(parse_cmd_line=False, conf_file=CONF_FILE)
#     t.define_tmux_vers("A")


def test_vc_low_suffix():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck("3.1b")
    assert vc.is_ok("3.1a") is True  # noqa


def test_vc_same():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck(3.0)
    assert vc.is_ok(3.0) is True  # noqa


def test_vc_same_suffix():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck("3.0a")
    assert vc.is_ok("3.0a") is True  # noqa


def test_vc_high_min():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck(3.1)
    assert vc.is_ok(3.2) is not True  # noqa


def test_vc_high_suffix():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck("3.1a")
    assert vc.is_ok("3.1b") is not True  # noqa


def test_vc_req_low():
    vc = VersionCheck(2.0, 2.4)
    assert vc.is_ok(2.3) is True  # noqa


def test_vc_req_low_suffix():
    vc = VersionCheck(2.0, "2.4b")
    assert vc.is_ok("2.4a") is True  # noqa


def test_vc_req_same():
    vc = VersionCheck(2.0, 2.4)
    assert vc.is_ok(2.4) is True


def test_vc_req_same_suffix():
    vc = VersionCheck(2.0, "2.4a")
    assert vc.is_ok("2.4a") is True


def test_vc_req_high():
    vc = VersionCheck(3.0, 2.4)
    assert vc.is_ok(2.5) is not True  # noqa


def test_vc_req_actual():
    vc = VersionCheck(3.0, 2.4)
    assert vc.get_actual() == "3.0"


def test_vc_req_get():
    vc = VersionCheck(3.0, 2.4)
    assert vc.get() == "2.4"


def test_vc_is_ok_no_min_vers():
    vc = VersionCheck(3.0)
    with pytest.raises(ValueError):
        vc.is_ok("3")


def test_vc_is_ok_maj_not_int():
    vc = VersionCheck(3.0)
    with pytest.raises(ValueError):
        vc.is_ok("a.b")
