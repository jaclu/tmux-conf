from tmux_conf.embedded_scripts import EmbeddedScripts
from tmux_conf.plugins import Plugins
from tmux_conf.vers_check import VersionCheck

CONF_FILE = "~/.tmux.conf"


def plugins_env():
    vc = VersionCheck(3.0)
    es = EmbeddedScripts(conf_file=CONF_FILE, use_embedded_scripts=True)
    plugins = Plugins(conf_file=CONF_FILE, vers_class=vc, es_class=es)
    return plugins


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