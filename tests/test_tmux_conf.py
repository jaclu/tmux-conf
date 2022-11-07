from tmux_conf.tmux_conf import TmuxConfig
from tmux_conf.utils import run_shell

CONF_FILE = "/tmp/tmux_test/tmux.conf"

BIND_CMD = "bind -N 'This is a note'  a  display 'that was a'"

CONTENT_LINE = "# Hello world"


class NotEmbedded(TmuxConfig):
    """We combine not embedded and content in the same class.
    They are used for separate tests so they dont overlap,
    just handy to use a single class"""

    use_embedded_scripts = False

    def content(self):
        self.write(CONTENT_LINE)


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
    if not (tmate_cmd := run_shell('command -v tmate')):
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
