import os
import shutil

import pytest
from src.tmux_conf.constants import XDG_CONFIG_HOME
from src.tmux_conf.embedded_scripts import EmbeddedScripts
from src.tmux_conf.plugins import Plugins
from src.tmux_conf.tmux_conf import TmuxConfig
from src.tmux_conf.vers_check import VersionCheck

from .utils_test import (
    install_plugins,
    tmux_conf_instance,
    tst_conf_base,
    tst_conf_file,
    tst_plugins_dir,
)

# from .utils_test import tst_conf_file  # CONF_FILE,
# from .utils_test import tst_plugins_dir  # PLUGINS_DIR,
# from .utils_test import install_plugins, tmp_conf_base, tmux_conf_instance


class PluginUnsafePluginDir(Plugins):
    def get_env(self):
        plugins_dir = os.path.expanduser("~")
        tpm_env = ""
        return plugins_dir, tpm_env


class Using2Plugins(TmuxConfig):
    plugin_handler = "manual"

    def content(self):
        """Needs an override"""

    def plugin_session_wizard(self):
        return ["27medkamal/tmux-session-wizard", 1, ""]

    def plugin_better_mouse_mode(self):
        return ["jaclu/tmux-better-mouse-mode", 99, ""]

    def plugin_no_slash(self):
        return ["no_slash", 1, ""]


class Using3Plugins(Using2Plugins):
    def plugin_prefix_highlight(self):
        return ["jaclu/tmux-prefix-highlight", 0, ""]


class DuplicatePlugins(Using2Plugins):
    def plugin_better_mouse_mode2(self):
        return ["jaclu/tmux-better-mouse-mode", 99, ""]


def plugins_env(conf_file, plugins_display=0):
    # f"{tmp_path}/tmux/tmux.conf"
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=conf_file, use_embedded_scripts=True)
    plugins = Plugins(
        conf_file=conf_file,
        vers_class=vc,
        es_class=es,
        plugins_display=plugins_display,
    )
    return plugins


def not_test_p_bad_display_param(tmp_path):
    tst_conf_file = f"{tmp_path}/tmux/tmux.conf"
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=tst_conf_file, use_embedded_scripts=True)
    with pytest.raises(ValueError):
        Plugins(conf_file=tst_conf_file, vers_class=vc, es_class=es, plugins_display=4)


def not_test_p_deploy_dir(tst_conf_file):
    plugins = plugins_env(tst_conf_file)
    ddir = plugins.get_plugin_dir()
    assert ddir.endswith("/plugins") is True


def not_test_p_limited_host_on(tst_conf_file):
    plugins = plugins_env(tst_conf_file)
    assert plugins.set_limited_host(True) is True


def not_test_p_limited_host_off(tst_conf_file):
    plugins = plugins_env(tst_conf_file)
    assert plugins.set_limited_host(False) is not True


def not_test_p_get_env(tst_conf_file):
    plugins = plugins_env(tst_conf_file)  # "~/.tmux.conf")
    ddir, _ = plugins.get_env()
    assert ddir == plugins.get_plugin_dir()


def not_test_p_get_plugin_dir_tmate():
    tc = plugins_env(conf_file="~/.tmate.conf")
    plugin_dir = tc.get_plugin_dir()
    assert plugin_dir == f"{os.getenv('HOME')}/.tmate/plugins"


def not_test_p_get_plugin_dir_xdg(tmp_path):
    tmp_conf_base = f"{tmp_path}/tmux"
    xdg_orig = os.environ.get(XDG_CONFIG_HOME, "")
    xdg_location = tmp_conf_base
    os.environ[XDG_CONFIG_HOME] = xdg_location
    plugins = plugins_env(f"{tmp_conf_base}/.tmux.conf")
    plugin_dir = plugins.get_plugin_dir()
    if xdg_orig:
        os.environ[XDG_CONFIG_HOME] = xdg_orig
    else:
        del os.environ[XDG_CONFIG_HOME]
    assert plugin_dir.find(xdg_location) > -1


def not_test_p_manual_handler(tst_conf_file):
    plugins = plugins_env(tst_conf_file)
    cont = plugins.mkscript_manual_deploy()
    assert cont[0].find("Manual Plugin Handling") > -1


def not_test_p_tpm_handler(tst_conf_file):
    plugins = plugins_env(tst_conf_file)
    cont = plugins.mkscript_tpm_deploy()
    assert cont[0].find("Tmux Plugin Manager") > -1


def test_p_parse(tst_conf_file):
    """Do a parse with no plugins defined"""
    plugins = plugins_env(tst_conf_file)
    assert not plugins.parse()


def test_p_def_conf_disp_info():
    plugins = plugins_env("~/.tmux.conf", plugins_display=1)
    with pytest.raises(SystemExit):
        plugins.display_info()


def bad_test_p_install(tst_conf_base, tst_conf_file, tst_plugins_dir):
    install_plugins(tst_conf_file)  # Manually install all plugins


def not_test_p_clear_plugins(tst_conf_base, tst_conf_file, tst_plugins_dir):
    cls = Using2Plugins

    #  Create a dummy dir, to ensure clear_plugins work as intended
    os.makedirs(f"{tst_conf_base}/foo", exist_ok=True)

    #  First clear all plugins installed
    tmux_conf_instance(cls, tst_conf_file, clear_plugins=True).run()

    # Ensure plugins dir is empty
    ddir = os.listdir(tst_plugins_dir)
    if len(ddir) > 0:
        raise ValueError("Plugin dir not empty!")

    # vc = VersionCheck(3.0)
    # es = EmbeddedScripts(conf_file=tst_conf_file, use_embedded_scripts=True)
    # Plugins(conf_file=tst_conf_file, vers_class=vc, es_class=es, clear_plugins=True)
    # # no exception is good enough for passing


def bad_test_p_installAgain(tmp_conf_base):
    """Install again to ensure plugins are present for further tests"""
    test_p_install(tmp_conf_base, cls=Using3Plugins)


def test_p_display(capfd, tst_conf_file):
    # tmux_conf_instance(cls, tst_conf_file, clear_plugins=True).run()
    t = tmux_conf_instance(Using2Plugins, tst_conf_file, plugins_display=2)
    with pytest.raises(SystemExit):
        t.run()

    out, _ = capfd.readouterr()
    # print(f">> out [{out}]")
    plugins_not_installed = []
    plugins_installed = []
    plugins_ignored = []
    gather_listed = gather_ignored = False
    for line in out.split("\n"):
        # print(f">> line [{line}]")
        if line.find("|  Min version") > -1:
            gather_listed = True
            # print(">> activating gather on line", line)
            continue
        if gather_listed:
            if not line.strip():
                gather_listed = False
                # print(">> canceled gather on line", line)
                continue
            plugin_name = line.split()[0]
            if line.find("Not installed") > -1:
                plugins_not_installed.append(plugin_name)
            else:
                plugins_installed.append(plugin_name)
        if line.find("vers|") == 0:
            gather_ignored = True
            continue
        if gather_ignored and line:
            plugin_name = line.split()[-1]
            plugins_ignored.append(plugin_name)

    # print(f">> installed     [{plugins_installed}]")
    # print(f">> not installed [{plugins_not_installed}]")
    # print(f">> ignored [{plugins_ignored}]")
    assert len(plugins_installed) == 1
    assert len(plugins_not_installed) == 1
    assert len(plugins_ignored) == 1


def not_test_p_display3(capfd):
    t = tmux_conf_instance(Using2Plugins, plugins_display=3)
    with pytest.raises(SystemExit):
        t.run()


def not_test_p_duplicate_plugin(capfd):
    with pytest.raises(SystemExit):
        tmux_conf_instance(DuplicatePlugins).run()
    out, _ = capfd.readouterr()
    assert out.find("defined more than once") > -1


def not_test_p_limited_host():
    t = tmux_conf_instance(Using2Plugins)
    t.is_limited_host = True
    try:
        t.run()
    except SystemExit:
        pass
    t.plugins.mkscript_tpm_deploy()


def not_test_p_suspicious_clear():
    t = tmux_conf_instance(Using2Plugins)
    t.plugins = PluginUnsafePluginDir(
        tst_conf_file,
        vers_class=t.vers,
        es_class=t.es,
        plugin_handler=t.plugin_handler,
        clear_plugins=False,
        plugins_display=0,
    )
    with pytest.raises(FileNotFoundError):
        t.plugins.clear()


def not_test_p_missing_plugin_dir():
    """Security checks to minimize risk of harmfull deletion"""
    if not tst_plugins_dir:
        raise SystemError("PLUGINS_DIR undefined")
    wrong_dir = "/moved_plugins"
    parts = "/".join(tst_plugins_dir.split("/")[:-1])
    target = parts + wrong_dir
    shutil.move(tst_plugins_dir, target)
    t = tmux_conf_instance(Using2Plugins)
    t.plugins.clear()
    if target.find(wrong_dir) != len(parts):
        raise ValueError(
            f"Not expected target [{target}] [{len(parts)} [{target.find(wrong_dir)}]"
        )
    shutil.rmtree(target)
