import os

import pytest
from src.tmux_conf.constants import XDG_CONFIG_HOME
from src.tmux_conf.embedded_scripts import EmbeddedScripts
from src.tmux_conf.plugins import Plugins
from src.tmux_conf.tmux_conf import TmuxConfig
from src.tmux_conf.vers_check import VersionCheck

from .common_vars import CONF_FILE

plugin_1 = "tmux-yank"
plugin_2 = "tmux-prefix-highlight"
plugin_3 = "tmux-menus"


class Plugins2(TmuxConfig):
    plugin_handler = "manual"

    def content(self):
        "Needs an override"
        pass

    def plugin_no_slash(self):
        return [f"no_slash", 1, ""]

    def plugin_yank(self):
        return [f"tmux-plugins/{plugin_1}", 1.9, ""]

    def plugin_prefix_highlight(self):
        return [f"tmux-plugins/{plugin_2}", 1.8, ""]


class Plugins3(Plugins2):
    def plugin_menus(self):
        return [f"jaclu/{plugin_3}", 99.0, ""]


def tmux_conf_instance(cls, clear_plugins=False, plugins_display=0):
    conf_base = "tmp/foo32/tmux"
    conf = f"{conf_base}/tmux.conf"
    t = cls(
        parse_cmd_line=False,
        conf_file=conf,
        replace_config=True,
        clear_plugins=clear_plugins,
        plugins_display=plugins_display,
    )
    return t


def plugins_env(conf_file=CONF_FILE, plugins_display=0):
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=conf_file, use_embedded_scripts=True)
    plugins = Plugins(
        conf_file=conf_file, vers_class=vc, es_class=es, plugins_display=plugins_display
    )
    return plugins


def test_p_bad_display():
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=CONF_FILE, use_embedded_scripts=True)
    with pytest.raises(ValueError):
        Plugins(conf_file=CONF_FILE, vers_class=vc, es_class=es, plugins_display=4)


def test_p_clear_plugind():
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=CONF_FILE, use_embedded_scripts=True)
    Plugins(conf_file=CONF_FILE, vers_class=vc, es_class=es, clear_plugins=True)
    # no exception is good enough for passing


def test_p_deploy_dir():
    plugins = plugins_env()
    ddir = plugins.get_plugin_dir()
    assert ddir.endswith("/plugins") is True


def test_p_limited_host_on():
    plugins = plugins_env()
    assert plugins.set_limited_host(True) is True


def test_p_limited_host_off():
    plugins = plugins_env()
    assert plugins.set_limited_host(False) is not True


def test_p_get_env():
    plugins = plugins_env("~/.tmux.conf")
    ddir, _ = plugins.get_env()
    assert ddir == plugins.get_plugin_dir()


def test_p_get_plugin_dir_tmate():
    tc = plugins_env(conf_file="~/.tmate.conf")
    plugin_dir = tc.get_plugin_dir()
    assert plugin_dir == f"{os.getenv('HOME')}/.tmate/plugins"


def test_p_get_plugin_dir_xdg():
    xdg_orig = os.environ.get(XDG_CONFIG_HOME, "")
    xdg_location = "/tmp/tmux_cont_test"
    os.environ[XDG_CONFIG_HOME] = xdg_location
    plugins = plugins_env()
    plugin_dir = plugins.get_plugin_dir()
    if xdg_orig:
        os.environ[XDG_CONFIG_HOME] = xdg_orig
    else:
        del os.environ[XDG_CONFIG_HOME]
    assert plugin_dir.find(xdg_location) > -1


def test_p_manual_header():
    plugins = plugins_env()
    cont = plugins.mkscript_manual_deploy()
    assert cont[0].find("Manual Plugin Handling") > -1


def test_p_tpm_header():
    plugins = plugins_env()
    cont = plugins.mkscript_tpm_deploy()
    assert cont[0].find("Tmux Plugin Manager") > -1


def test_p_parse():
    """Do a parse with no plugins defined"""
    plugins = plugins_env()
    assert not plugins.parse()


def test_p_def_conf_disp_info():
    plugins = plugins_env("~/.tmux.conf", plugins_display=1)
    with pytest.raises(SystemExit):
        plugins.display_info()


def test_p_install():
    conf_base = "/tmp/foo32/tmux"
    conf = f"{conf_base}/tmux.conf"

    #  First clear all plugins installed
    tmux_conf_instance(Plugins3, clear_plugins=True).run()

    print("---  Manually install all plugins  ---")
    os.system(f"cut -c3- {conf} | /usr/local/bin/bash -s activate_plugins_mamually")


@pytest.mark.parametrize(
    "display",
    [
        (1),
        (2),
        (3),
    ],
)
def test_p_display(capfd, display):

    t = tmux_conf_instance(Plugins2, plugins_display=display)
    # t.is_limited_host = True
    try:
        t.run()
    except SystemExit:
        pass
    # t.plugins.mkscript_tpm_deploy()
    out, err = capfd.readouterr()
    print(">> err", out)
    assert 2 == 5
