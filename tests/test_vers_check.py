from src.tmux_conf.vers_check import VersionCheck


def test_vc_low():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck(3.0)
    assert vc.is_ok(2.9) is True  # noqa


def test_vc_same():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck(3.0)
    assert vc.is_ok(3.0) is True  # noqa


def test_vc_high():
    # conf_file = "~/.tmux.conf"
    vc = VersionCheck(3.0)
    assert vc.is_ok(3.1) is not True  # noqa


def test_vc_req_high():
    vc = VersionCheck(3.0, 2.4)
    assert vc.is_ok(2.5) is not True  # noqa


def test_vc_req_same():
    vc = VersionCheck(3.0, 2.4)
    assert vc.is_ok(2.4) is True


def test_vc_req_actual():
    vc = VersionCheck(3.0, 2.4)
    assert vc.get_actual() == "3.0"


def test_vc_req_get():
    vc = VersionCheck(3.0, 2.4)
    assert vc.get() == "2.4"
