import os

_conf_base = "/tmp/foo32/tmux"
CONF_FILE = f"{_conf_base}/tmux.conf"
PLUGINS_DIR = f"{_conf_base}/plugins"


def remove_conf_file():
    if CONF_FILE.find("tmp") == 1 and os.path.exists(CONF_FILE):
        os.remove(CONF_FILE)


def install_plugins():
    os.system(f"cut -c3- {CONF_FILE} | bash -s activate_plugins_mamually")


def tmux_conf_instance(cls, tmux_version="", clear_plugins=False, plugins_display=0):
    t = cls(
        parse_cmd_line=False,
        tmux_version=tmux_version,
        conf_file=CONF_FILE,
        replace_config=True,
        clear_plugins=clear_plugins,
        plugins_display=plugins_display,
    )
    return t
