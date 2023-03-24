import os
import shutil

import pytest
from src.tmux_conf import TmuxConfig
from src.tmux_conf.utils import run_shell

from .utils import CONF_FILE, install_plugins, remove_conf_file, tmux_conf_instance

CONTENT_LINE = "# Hello world"
PLUGIN_SOURCE = "jaclu"
PLUGIN_NAME = "tmux-prefix-highlight"


class WithContent(TmuxConfig):
    tst_content = "# dummy content"

    def content(self):
        self.write(self.tst_content)


class NotEmbedded(WithContent):
    """We combine not embedded and content in the same class.
    They are used for separate tests so they dont overlap,
    just handy to use a single class"""

    use_embedded_scripts = False


class PluginsSample(WithContent):
    """Test class ensuring plugins are only present at the intended
    versions"""

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

    def plugin_session_wizard(self):  # 3.2
        return ["27medkamal/tmux-session-wizard", 3.2, "#  Default trigger: <prefix> T"]


class PluginsDisabled(PluginsSample):
    """Test class ensuring no plugins show up if plugin_handler is
    disabled"""

    plugin_handler = ""


class PluginsManual(PluginsSample):
    """Test class ensuring no plugins show up if plugin_handler is
    disabled"""

    plugin_handler = "manual"


class PluginsDuplicated(PluginsSample):
    def plugin_prefix_highlight2(self):
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


def tc_env(conf_file=CONF_FILE):
    tc = TmuxConfig(parse_cmd_line=False, conf_file=conf_file)
    return tc


def prep_plugin_class(cls, version="2.8", plugins_display=0):
    t = tmux_conf_instance(
        cls=cls, tmux_version=version, plugins_display=plugins_display
    )
    # ps = cls(parse_cmd_line=False, conf_file=CONF_FILE, tmux_version=version)
    t.plugins.scan(t.list_plugin_methods())
    return t


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


#
#  Cant be run inside VSCode ATM...
#
cfb = os.environ.get("__CFBundleIdentifier")
if not cfb or cfb.find("VSCode") < 0:

    def test_tc_parse_cmd_line():
        remove_conf_file()
        t = TmuxConfig()
        with pytest.raises(OSError):
            t.run()


def test_tc_content_needs_overloading():
    t = TmuxConfig(parse_cmd_line=False)
    with pytest.raises(NotImplementedError) as exc:
        t.content()
    assert exc.value.args[0] == "content() must be defined in sub-class!"


def test_tc_repeated_calls_to_edit_config_coverage():
    t = TmuxConfig(parse_cmd_line=False)
    t.edit_config()
    t.edit_config()


def test_tc_btick():
    t = tmux_conf_instance(cls=WithContent)
    t.tst_content = "# one btick `"
    with pytest.raises(SyntaxError) as exc:
        t.run()
    assert exc.value.args[0].find("Un-escaped back-ticks can not be present") > -1


#
#  Handle notes
#
def test_tc_note_unchanged():
    bind_cmd = "bind -N 'This is a note'  a  display 'that was a'"
    tc = tc_env()
    tc.define_tmux_vers(vers="3.2")
    assert tc.filter_note(bind_cmd) == [bind_cmd]


def test_tc_note_as_comment():
    #  Also ensure spaces > 2 after note are disgarded
    tc = tc_env()
    tc.define_tmux_vers(vers="2.8")
    assert tc.filter_note("bind -N 'This is a note'    a display 'that was a'") == [
        "",
        "#  This is a note",
        "bind  a display 'that was a'",
    ]


def test_tc_note_removed():
    tc = tc_env()
    tc.define_tmux_vers(vers="2.8")
    tc.use_notes_as_comments = False
    assert tc.filter_note("bind -N 'This is a note'  a  display 'that was a'") == [
        "bind  a  display 'that was a'"
    ]


def test_tc_note_ends_with_N():
    #  Ensure empty -N is removed
    tc = tc_env()
    tc.define_tmux_vers(vers="2.8")
    assert tc.filter_note("dummy line -N") == ["dummy line"]


def test_tc_note_single_word():
    #  needed for coverage
    tc = tc_env()
    tc.define_tmux_vers(vers="2.8")
    tc.filter_note("dummy line -N notice")


def test_tc_note_extra_N_is_purged():
    #  Ensure extra -N is disgarded
    note = "missing feature"
    cmd = "dummy line"
    cmd_rest = 'M display "mouse toggle needs 2.1"'
    line = f'{cmd} -N      "{note}" {cmd_rest}'
    tc = tc_env()
    tc.define_tmux_vers(vers="2.8")
    assert tc.filter_note(f'{line} -N "another comment"') == [
        "",
        f"#  {note}",
        f"{cmd} {cmd_rest}",
    ]


#
#  Conf file
#
def test_tc_conf_file_not_replace(capfd):
    t = TmuxConfig(parse_cmd_line=False, replace_config=False)
    with pytest.raises(OSError):
        t.run()
    out, _ = capfd.readouterr()
    assert out.find("Do you wish to replace the default config file (y/n)?") > -1


def test_tc_conf_file_create_default(capfd):
    def_conf_file = os.path.expanduser("~/.tmux.conf")
    tmp_conf_file = os.path.expanduser("~/.tmux.conf.orig")
    if os.path.exists(def_conf_file):
        if os.path.exists(tmp_conf_file):
            #  Ensure we start with an empty file
            os.remove(tmp_conf_file)
        shutil.move(def_conf_file, tmp_conf_file)

    t = TmuxConfig(parse_cmd_line=False)
    with pytest.raises(OSError):
        t.run()
    out, _ = capfd.readouterr()
    if os.path.exists(tmp_conf_file):
        shutil.move(tmp_conf_file, def_conf_file)
    assert out.find("Do you wish to create a default config file (y/n)?") > -1


def test_tc_conf_file_no_write(capfd):
    cf_file = "/var/root/foo/tmux.conf"
    with pytest.raises(OSError):
        t = TmuxConfig(parse_cmd_line=False, conf_file=cf_file)
        t.run()
    out, _ = capfd.readouterr()
    assert (
        out.find("ERROR: read only file system reported") > -1
        or out.find("ERROR: Could not write to config file") > -1
    )


def test_tc_conf_file_not_replace_other_conf(capfd):
    t = TmuxConfig(parse_cmd_line=False, conf_file=CONF_FILE)
    with pytest.raises(OSError):
        t.run()
    out, _ = capfd.readouterr()
    assert out.find(f"Do you wish to replace {CONF_FILE} (y/n)?") > -1


def test_tc_conf_file_not_embedded():
    tc = NotEmbedded(parse_cmd_line=False, conf_file=CONF_FILE)
    tc.conf_file_header()
    with open(os.path.expanduser(CONF_FILE), encoding="utf-8") as f:
        line = f.readline()  # Just get 1st line
    assert line == "#\n"
    tc.remove_conf_file()


def test_tc_conf_file_is_embedded():
    tc = tc_env()
    tc.conf_file_header()
    with open(os.path.expanduser(CONF_FILE), encoding="utf-8") as f:
        line = f.readline()  # Just get 1st line
    assert line.find("EMBEDDED-SCRIPTS-STARTING-POINT") > -1
    tc.remove_conf_file()


def test_tc_conf_file_header_and_content():
    """Check that TMUX_CONF & TMUX_BIN are correctly set"""
    fname = os.path.expanduser(CONF_FILE)
    tc = NotEmbedded(parse_cmd_line=False, conf_file=CONF_FILE)
    tc.replace_config = True
    tc.conf_file_header()
    tc.run()
    with open(os.path.expanduser(fname), encoding="utf-8") as f:
        lines = f.readlines()
    tmux_bin_found = False
    edit_conf_found = False
    for line in lines:
        if line.find("TMUX_CONF=") > -1:
            conf_file = line.split("=")[1].strip()
            assert conf_file == f'"{fname}"'
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


#
#  tmux bin versions
#
def test_tc_bin_not_found():
    bad_tmux = "tmmuxx"
    with pytest.raises(SyntaxError) as exc:
        TmuxConfig(parse_cmd_line=False, conf_file=CONF_FILE, tmux_bin=bad_tmux)
    assert exc.value.args[0] == f"tmux cmd not found: {bad_tmux}"


def test_tc_bin_empty():
    t = TmuxConfig(parse_cmd_line=False, conf_file=CONF_FILE)
    with pytest.raises(SyntaxError) as exc:
        t.use_tmux_bin("")
    assert exc.value.args[0] == "cmd empty"


def test_tc_bin_incorrect():
    wrong_bin = "python3"  # must exist even if not tmux...
    t = TmuxConfig(parse_cmd_line=False, conf_file=CONF_FILE)
    with pytest.raises(SystemExit) as exc:
        t.use_tmux_bin(wrong_bin)
    assert exc.value.args[0] == f"ERROR: tmux bin seems invalid: {wrong_bin}"


def test_tc_bin_auto_find():
    #  coverage
    t = TmuxConfig(parse_cmd_line=False, conf_file=CONF_FILE)
    t.define_tmux_vers(tmux_bin="")
    t.find_cmd_2()
    t.find_cmd_3()


def test_tc_non_default_version():
    other_version = "4.0"
    remove_conf_file()

    t = PluginsSample(
        parse_cmd_line=False,
        conf_file=CONF_FILE,
        tmux_version=other_version,
        plugins_display=3,
    )
    with pytest.raises(SystemExit):
        t.run()


def test_tc_too_old_for_plugins(capfd):
    ancient_vers = "1.0"
    with pytest.raises(SystemExit):
        TmuxConfig(parse_cmd_line=False, tmux_version=ancient_vers, plugins_display=1)
    out, _ = capfd.readouterr()
    assert out.find("Config has been requested for another version of tmux") > -1
    assert out.find(f"requested vers:  {ancient_vers}") > -1
    assert out.find("might give some errors!") > -1


#
#  Working with plugins
#
def test_tc_plugin_found():
    t = prep_plugin_class(cls=PluginsSample, version="2.4")
    assert t.plugins.found() == [PLUGIN_NAME]
    assert t.plugins.found(short_name=False) == [f"{PLUGIN_SOURCE}/{PLUGIN_NAME}"]


def test_tc_plugin_write():
    t = prep_plugin_class(cls=PluginsSample)
    t.run()
    install_plugins()


def test_tc_plugin_display_2():
    t = prep_plugin_class(cls=PluginsSample, plugins_display=2)
    with pytest.raises(SystemExit):
        t.run()
    # out, _ = capfd.readouterr()
    # print(f">> out [{out}]")
    # assert 1 == 2


def test_tc_plugin_display_3():
    t = prep_plugin_class(cls=PluginsSample, plugins_display=3)
    with pytest.raises(SystemExit):
        t.run()


def test_tc_plugin_unavailable():
    t = prep_plugin_class(cls=PluginsSample, version="2.0")
    assert not t.plugins.found()
    assert not t.plugins.found(short_name=False)


def test_tc_plugins_disabled():
    t = prep_plugin_class(cls=PluginsDisabled, version="2.4")
    assert not t.plugins.found()
    assert not t.plugins.found(short_name=False)


def test_tc_plugin_duplicate():
    with pytest.raises(SystemExit):
        prep_plugin_class(cls=PluginsDuplicated, version="2.4")


#
#  Checks that only plugins of matching version are selected
#
@pytest.mark.parametrize(
    "vers, plugins_expected",
    [
        (2.2, 0),
        (2.8, 1),
        (3.2, 2),
    ],
)
def test_tc_plugins_display_info(vers, plugins_expected, capsys):
    ps = prep_plugin_class(cls=PluginsSample, version=vers)
    #  to test both verbose and not for plugin display in order to
    #  increase coverage
    if plugins_expected == 2:
        ps.plugins._plugins_display = 3
    elif plugins_expected == 1:
        ps.plugins._plugins_display = 2
    try:
        ps.plugins.display_info()
    except SystemExit:
        #  display_info() terminates prog after displaying info,
        #  this forces continuation
        pass
    captured = capsys.readouterr()
    do_count = False
    plugins_found = 0
    for line in captured.out.split("\n"):
        print(line)
        if line.find("Plugins ignored") > -1 or line.find("Unused plugins found") > -1:
            #  Stop counting when ignored list starts
            do_count = False
        if do_count and line.find(" - ") > -1:
            plugins_found += 1
        if line.find("|  Min") > -1:
            #  Start counting after header before used plugins
            do_count = True
    assert plugins_found == plugins_expected


@pytest.mark.parametrize(
    "plugin_cls",
    [
        (PluginsSample),
        (PluginsManual),
    ],
)
def test_tc_plugins_parse(plugin_cls):
    ps = prep_plugin_class(cls=plugin_cls)
    output = ps.plugins.parse()
    assert isinstance(output, list)


#
#  tmate tests
#
def test_tc_tmate():
    TmuxConfig(parse_cmd_line=False, conf_file="~/.tmux.conf", tmux_bin="tmate")


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


def not_tc_tmate_get_env():
    tc = tc_env(conf_file="~/.tmate.conf")
    #  This assumes there is a tmate in PATH
    if not (tmate_cmd := run_shell("command -v tmate")):
        return  # Can't do this test
    tc.use_tmux_bin(tmate_cmd)
    plugins_dir, _ = tc.plugins.get_env()
    assert plugins_dir == f"{os.getenv('HOME')}/.tmate/plugins"


def test_tc_tmate_get_env():
    tc = tc_env(conf_file="~/.tmate.conf")
    #  This assumes there is a tmate in PATH
    if not (tmate_cmd := run_shell("command -v tmate")):
        return  # Can't do this test
    tc.use_tmux_bin(tmate_cmd)
    plugins_dir, _ = tc.plugins.get_env()
    assert plugins_dir == f"{os.getenv('HOME')}/.tmate/plugins"
