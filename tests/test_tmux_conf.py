from common_vars import CONF_FILE

from tmux_conf.tmux_conf import TmuxConfig
from tmux_conf.utils import run_shell

BIND_CMD = "bind -N 'This is a note'  a  display 'that was a'"
CONTENT_LINE = "# Hello world"
PLUGIN_SOURCE = "jaclu"
PLUGIN_NAME = "tmux-prefix-highlight"


class PluginsSample(TmuxConfig):
    def content(self):
        self.write("# dummy content")

    def plugin_prefix_highlight(self):
        #
        #  Highlights when you press tmux prefix key and
        #  when copy/sync mode is active.
        #
        conf = """
        set -g @prefix_highlight_show_copy_mode  on
        set -g @prefix_highlight_copy_mode_attr  "fg=black,bg=yellow,bold"
        set -g @prefix_highlight_show_sync_mode  on
        set -g @prefix_highlight_sync_mode_attr "fg=black,bg=orange,blink,bold"
        """
        return [f"{PLUGIN_SOURCE}/{PLUGIN_NAME}", 2.4, conf]


class PluginsDisabled(PluginsSample):
    plugin_handler = ""


class NotEmbedded(TmuxConfig):
    """We combine not embedded and content in the same class.
    They are used for separate tests so they dont overlap,
    just handy to use a single class"""

    use_embedded_scripts = False

    def content(self):
        self.write(CONTENT_LINE)


def prep_plugin_class(cls, version):
    ps = cls(parse_cmd_line=False, conf_file=CONF_FILE, tmux_version=version)
    ps.plugins.scan(ps.list_plugin_methods())
    return ps


def tc_env():
    tc = TmuxConfig(parse_cmd_line=False, conf_file=CONF_FILE)
    return tc


def test_tc_vers_ok_low():
    tc = tc_env()
    assert tc.vers_ok(1.0) is True


def test_tc_vers_ok_high():
    tc = tc_env()
    assert tc.vers_ok(99) is not True


def test_tc_find_tmux_bin():
    tc = tc_env()
    assert tc.find_tmux_bin() is True


def test_tc_is_tmux_bin():
    tc = tc_env()
    #  This assumes there is a tmux in PATH
    assert tc.is_tmux_bin("tmux") is True


def test_tc_is_not_tmate():
    tc = tc_env()
    assert tc.is_tmate() is not True


def test_tc_is_tmate():
    tc = tc_env()
    #  This assumes there is a tmate in PATH
    if not (tmate_cmd := run_shell("command -v tmate")):
        return  # Can't do this test
    tc.use_tmux_bin(tmate_cmd)
    assert tc.is_tmate() is True


def test_tc_filter_note():
    tc = tc_env()
    tc.define_tmux_vers(vers="3.2")
    assert tc.filter_note(BIND_CMD) == [BIND_CMD]


def test_tc_filter_note_as_comment():
    tc = tc_env()
    tc.define_tmux_vers(vers="2.8")
    assert tc.filter_note("bind -N 'This is a note'  a  display 'that was a'") == [
        "",
        "#  This is a note",
        "bind  a  display 'that was a'",
    ]


def test_tc_filter_note_not_as_comment():
    tc = tc_env()
    tc.define_tmux_vers(vers="2.8")
    tc.use_notes_as_comments = False
    assert tc.filter_note("bind -N 'This is a note'  a  display 'that was a'") == [
        "bind  a  display 'that was a'"
    ]


def test_tc_conf_file_not_embedded():
    tc = NotEmbedded(parse_cmd_line=False, conf_file=CONF_FILE)
    tc.conf_file_header()
    with open(CONF_FILE, encoding="utf-8") as f:
        line = f.readline()  # Just get 1st line
    assert line == "#\n"
    tc.remove_conf_file()


def test_tc_conf_file_is_embedded():
    tc = tc_env()
    tc.conf_file_header()
    with open(CONF_FILE, encoding="utf-8") as f:
        line = f.readline()  # Just get 1st line
    assert line.find("EMBEDDED-SCRIPTS-STARTING-POINT") > -1
    tc.remove_conf_file()


def test_tc_conf_file_header_and_content():
    """Check that TMUX_CONF & TMUX_BIN are correctly set"""
    tc = NotEmbedded(parse_cmd_line=False, conf_file=CONF_FILE)
    tc.replace_config = True
    tc.conf_file_header()
    tc.run()
    with open(CONF_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    tmux_bin_found = False
    edit_conf_found = False
    for line in lines:
        if line.find("TMUX_CONF=") > -1:
            conf_file = line.split("=")[1].strip()
            assert conf_file == f'"{CONF_FILE}"'
        if line.find("TMUX_BIN=") > -1:
            tmux_bin = line.split("=")[1].strip()
            assert tmux_bin == f'"{tc.tmux_bin}"'
            tmux_bin_found = True
        if line.find("Edit config") > -1:
            edit_conf_found = True
        if line.find(CONTENT_LINE) > -1:
            # This should come after the TMUX_BIN line
            # and before the "Edit config" line
            assert tmux_bin_found is True
            assert edit_conf_found is not True

    assert edit_conf_found is True
    tc.remove_conf_file()


def test_tc_plugin_found():
    ps = prep_plugin_class(cls=PluginsSample, version=2.4)
    assert ps.plugins.found() == [PLUGIN_NAME]
    assert ps.plugins.found(short_name=False) == [f"{PLUGIN_SOURCE}/{PLUGIN_NAME}"]


def test_tc_plugin_unavailable():
    ps = prep_plugin_class(cls=PluginsSample, version=2.0)
    assert not ps.plugins.found()
    assert not ps.plugins.found(short_name=False)


def test_tc_plugins_disabled():
    ps = prep_plugin_class(cls=PluginsDisabled, version=2.4)
    assert not ps.plugins.found()
    assert not ps.plugins.found(short_name=False)
