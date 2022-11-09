import os

import pytest

from src.tmux_conf.embedded_scripts import EmbeddedScripts
from src.tmux_conf.plugins import Plugins
from src.tmux_conf.vers_check import VersionCheck

from .common_vars import CONF_FILE


def plugins_env(conf_file=CONF_FILE):
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=conf_file, use_embedded_scripts=True)
    plugins = Plugins(conf_file=conf_file, vers_class=vc, es_class=es)
    return plugins


def test_plugins_bad_display():
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=CONF_FILE, use_embedded_scripts=True)
    with pytest.raises(ValueError):
        Plugins(conf_file=CONF_FILE, vers_class=vc, es_class=es, plugins_display=4)


def test_plugins_clear_plugind():
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=CONF_FILE, use_embedded_scripts=True)
    Plugins(conf_file=CONF_FILE, vers_class=vc, es_class=es, clear_plugins=True)
    # no exception is good enough for passing


def test_plugins_deploy_dir():
    plugins = plugins_env()
    ddir = plugins.get_deploy_dir()
    assert ddir.endswith("/plugins") is True


def test_plugins_limited_host_on():
    plugins = plugins_env()
    assert plugins.set_limited_host(True) is True


def test_plugins_limited_host_off():
    plugins = plugins_env()
    assert plugins.set_limited_host(False) is not True


def test_plugins_get_env():
    plugins = plugins_env("~/.tmux.conf")
    ddir, _ = plugins.get_env()
    assert ddir == plugins.get_deploy_dir()


def test_plugins_get_env_tmate():
    tc = plugins_env(conf_file="~/.tmate.conf")
    ddir, _ = tc.get_env()
    assert ddir == f"{os.getenv('HOME')}/.tmate/plugins"


def test_plugins_get_env_xdg():
    plugins = plugins_env()
    ddir, _ = plugins.get_env()
    assert ddir == plugins.get_deploy_dir()


def test_plugins_manual_header():
    plugins = plugins_env()
    cont = plugins.mkscript_manual_deploy()
    assert cont[0].find("Manual Plugin Handling") > -1


def test_plugins_tpm_header():
    plugins = plugins_env()
    cont = plugins.mkscript_tpm_deploy()
    assert cont[0].find("Tmux Plugin Manager") > -1


def test_plugins_parse():
    """Do a parse with no plugins defined"""
    plugins = plugins_env()
    assert not plugins.parse()
