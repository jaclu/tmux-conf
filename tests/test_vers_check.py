import pytest
from src.tmux_conf.vers_check import VersionCheck


def test_vc_maj_not_int():
    with pytest.raises(ValueError):
        VersionCheck("a.b")


def test_vc_is_ok_maj_not_int():
    vc = VersionCheck(3.2)
    with pytest.raises(ValueError):
        vc.is_ok("a")


def test_vc_bad_min():
    with pytest.raises(ValueError):
        VersionCheck("3.b")


def test_vc_same():
    vc = VersionCheck(3.2)
    assert vc.is_ok(3.2) is True  # noqa


def test_vc_same_suffix():
    vc = VersionCheck("3.2a")
    assert vc.is_ok("3.2a") is True  # noqa


def test_vc_maj_high():
    vc = VersionCheck(3.1)
    assert vc.is_ok(4.0) is not True  # noqa


def test_vc_maj_high_int_str():
    vc = VersionCheck(3.0)
    assert vc.is_ok("4") is not True


def test_vc_maj_low():
    vc = VersionCheck(3.1)
    assert vc.is_ok(2.0) is True  # noqa


def test_vc_min_high():
    vc = VersionCheck(3.2)
    assert vc.is_ok(3.3) is not True  # noqa


def test_vc_min_low():
    vc = VersionCheck(3.2)
    assert vc.is_ok(3.0) is True  # noqa


def test_vc_suffix_high():
    vc = VersionCheck("3.1a")
    assert vc.is_ok("3.1b") is not True  # noqa


def test_vc_suffix_low():
    vc = VersionCheck("3.1b")
    assert vc.is_ok("3.1a") is True  # noqa


def test_vc_req_actual():
    vc = VersionCheck(3.0, 2.4)
    assert vc.get_actual() == "3.0"


def test_vc_req_get():
    vc = VersionCheck(3.0, 2.4)
    assert vc.get() == "2.4"


def test_vc_req_same():
    vc = VersionCheck(2.0, 2.4)
    assert vc.is_ok(2.4) is True


def test_vc_req_same_suffix():
    vc = VersionCheck(2.0, "2.4a")
    assert vc.is_ok("2.4a") is True


def test_vc_req_high():
    vc = VersionCheck(2.0, 2.4)
    assert vc.is_ok(2.5) is not True


def test_vc_req_high_suffix():
    vc = VersionCheck(2.0, 2.4)
    assert vc.is_ok("2.4a") is not True


def test_vc_req_inbetween():
    vc = VersionCheck(2.0, 2.4)
    assert vc.is_ok(2.2) is True


def test_vc_req_inbetween_suffix():
    vc = VersionCheck(2.0, 2.4)
    assert vc.is_ok("2.2a") is True


def test_vc_req_low():
    vc = VersionCheck(3.0, 2.4)
    assert vc.is_ok(2.3) is True


def test_vc_req_low_suffix():
    vc = VersionCheck(3.0, 2.4)
    assert vc.is_ok("2.3a") is True


def test_vc_req_low_both():
    vc = VersionCheck(3.0, 2.4)
    assert vc.is_ok(2.2) is True


def test_vc_req_low_both_suffix():
    vc = VersionCheck(3.0, 2.4)
    assert vc.is_ok("2.2a") is True


def test_vc_missing_subvers():
    vc = VersionCheck(3)
    assert vc.is_ok(3.0) is True


def test_vc_missing_subvers_str():
    vc = VersionCheck("3")
    assert vc.is_ok(3.0) is True


def test_vc_normalize_vers():
    vc = VersionCheck(3.0)
    assert vc.normalize_vers(2) == "2.0"


def test_vc_vers_bad_init():
    with pytest.raises(ValueError):
        vc = VersionCheck("qwerty")
