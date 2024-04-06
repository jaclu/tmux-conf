import os

import pytest


def remove_conf_file():
    if CONF_FILE.find("tmp") == 1 and os.path.exists(CONF_FILE):
        os.remove(CONF_FILE)


def install_plugins(conf_file):
    # if run_shell("command -v bash"):
    os.system(f"cut -c3- {conf_file} | "
              "bash -s activate_plugins_mamually")


def tmux_conf_instance(cls, tmux_conf, tmux_version="",
                       clear_plugins=False, plugins_display=0):
    t = cls(
        parse_cmd_line=False,
        tmux_version=tmux_version,
        conf_file=tmux_conf,
        replace_config=True,
        clear_plugins=clear_plugins,
        plugins_display=plugins_display,
    )
    return t


# @pytest.fixture(scope="session")
# def tmp_conf_base(tmp_path_factory):
#     base_dir = tmp_path_factory.mktemp("tmp-tmux-conf")
#     return base_dir


# def tst_conf_file(tmp_path_factory) -> str:
#     return str(os.path.join(tmp_path_factory, "tmux.conf"))


@pytest.fixture()
def tst_conf_base(tmp_path):
    base_path = f"{tmp_path}/tmux"
    os.mkdir(base_path)
    return base_path


@pytest.fixture()
def tst_conf_file(tst_conf_base):
    return f"{tst_conf_base}/tmux.conf"


@pytest.fixture()
def tst_plugins_dir(tst_conf_base):
    plugin_dir = f"{tst_conf_base}/plugins"
    os.mkdir(plugin_dir)
    return plugin_dir


# def tst_plugins_dir(tmp_conf_base) -> str:
#     return str(os.path.join(tmp_conf_base, "plugins"))

_conf_base = "/tmp/foo32/tmux"
CONF_FILE = f"{_conf_base}/tmux.conf"
PLUGINS_DIR = f"{_conf_base}/plugins"
