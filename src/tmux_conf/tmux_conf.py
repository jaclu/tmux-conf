#
#  Copyright (c) 2022-2024: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#
#  See the README.md in the repository for more info
#
#  All paths stored internally are done so with ~ expanded
#

# pylint: disable=C0116

"""Class that generates a .tmux.conf"""

# from datetime import datetime
import datetime
import os
import shutil
import sys
from pathlib import Path
from typing import Union

import __main__

from .constants import __version__
from .embedded_scripts import EmbeddedScripts
from .exceptions import TmuxConfNotTmuxCommand
from .plugins import Plugins
from .utils import btick_unescaped, parse_cmdline, run_shell, verify_conf_file_usable
from .vers_check import VersionCheck


# pylint: disable=too-many-arguments,too-many-instance-attributes,too-many-public-methods
class TmuxConfig:
    """Class that generates a .tmux.conf"""

    #
    #  I have forked a tpm that uses TPM_BIN to use the right tmux
    #  context. If you just use one version of tmux, this does not
    #  matter, but if you experiment with various versions,
    #  this is essential. It ensures tpm and other processes started
    #  inside tmux use the running tmux bin.
    #
    #  My fork also reports more detailed progress on what plugin is
    #  processed
    #
    #  set this to 'jaclu/tpm' if you want to try that one!
    #  set it to "manual" if you don't want to use tpm.
    #  set it to '' if you do not want to use plugins at all.
    #
    plugin_handler: str = "tmux-plugins/tpm"

    #
    #  If true and tmux is < 3.1 thus not supporting -N bind notes
    #  this extracts the note and inserts it before the line as a comment.
    #  If false, the note is just discarded.
    #
    use_notes_as_comments: bool = True

    #
    #  If false, scripts are saved in scripts/ inside the tmux conf dir
    #
    use_embedded_scripts: bool = True

    #
    #  Indicates if this host is low on performance, don't enable
    #  demanding plugins etc, I use this on my iSH nodes.
    #  This must be set during __init__(). It is assumed to already been
    #  set to the intended state when self.run() is done.
    #
    #  The only usage of this in this package is to propagate it to
    #  the plugin handler, indicating as plugins are installed and
    #  activated, since this might take a noticeable time on slower nodes.
    #  It is also available in derived plugin_ methods
    #
    #  Other usages of this is up to implementation classes
    #
    is_limited_host: bool = False

    lib_version: str = __version__

    use_debug_log = False  # if True, debug log will be printed

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        parse_cmd_line: bool = True,
        #
        #  if parse_cmd_line is True all other parameters are ignored
        #
        conf_file: str = "~/.tmux.conf",  # where to store conf file
        tmux_bin: str = "tmux",  # Default binary, if none given
        tmux_version: str = "",
        replace_config: bool = False,  # replace config with no prompt
        clear_plugins: bool = False,  # remove all current plugins
        plugins_display: int = 0,  # Display info about plugins
        # then terminate
    ):
        if parse_cmd_line:
            args = parse_cmdline(sys.argv[1:])
            conf_file = args.conf_file
            tmux_bin = args.tmux_bin
            tmux_version = args.forced_version
            replace_config = args.replace
            clear_plugins = args.clear_plugins
            plugins_display = args.plugins_display

        print(f"Processing: {__main__.__file__}")
        self.tmux_bin = ""
        self.e_c_has_been_called = False
        self._parsing_note = False  # Only enabled during parsing of bind note
        # config file will only be written to if self.write_enable(True) has been set
        self._write_enabled = False
        self.init_debug_log()

        #  can't use self.is_tmate() at this point, since self.tmux_bin
        #  is not yet set
        if tmux_bin.find("tmate") > -1:
            #  Set tmate defaults
            if not tmux_version:
                tmux_version = "2.4"
            if conf_file == "~/.tmux.conf":
                #  Override default config
                conf_file = "~/.tmate.conf"
                replace_config = True

            if self.plugin_handler:
                #  tmate only supports manual plugin handling
                self.plugin_handler = "manual"

        self.conf_file = verify_conf_file_usable(conf_file)

        self.use_tmux_bin(tmux_bin, tmux_version)
        if tmux_version and (tmux_version != self.vers.get()):  # type: ignore
            # self.define_tmux_vers(tmux_version)
            if not self.is_tmate():
                #
                #  Only display off version info when bin is tmux
                #
                print()
                print(
                    "Config has been requested for another version of tmux,"
                    + " than the one used to generate this.\n"
                    + "Since the config file will point to the tmux used, "
                    + "this might cause problems\n"
                    + f"\ttmux vers is:    {self.vers.get_actual()}\n"
                    + f"\trequested vers:  {self.vers.get()}"
                )
                print()
                print("WARNING: Running this config with the current tmux")
                print("         might give some errors!")
                print()
        self.replace_config = replace_config
        self.plugins_display = plugins_display

        self.es = EmbeddedScripts(
            conf_file=self.conf_file,
            vers_class=self.vers,  # type: ignore
            use_embedded_scripts=self.use_embedded_scripts,
        )

        #
        #  If current tmux is too old to handle tpm plugins,
        #  disable plugins entirely
        #
        if not self.vers_ok("1.9") and self.plugin_handler:
            # tpm not available before 1.9, since it was defined, ensure
            # this is set to manual
            self.plugin_handler = "manual"

        self.plugins = Plugins(
            conf_file=self.conf_file,
            vers_class=self.vers,  # type: ignore
            es_class=self.es,
            plugin_handler=self.plugin_handler,
            clear_plugins=clear_plugins,
            plugins_display=plugins_display,
        )

    # ================================================================
    #
    #  Needs overloading
    #
    # ================================================================

    def content(self) -> None:  # NotImplementedError
        """This method is expected to use self.write() to generate the
        majority of the config file.
        Plugins can be handled separately (check the README) or if you
        prefer you can just drop your current code doing that here.
        """
        raise NotImplementedError("content() must be defined in sub-class!")

    # ================================================================
    #
    #  Optional overloading
    #
    # ================================================================

    def local_overrides(self) -> None:
        """
        Applies local configuration overrides, executed after all other
        configuration steps. The only exception is status bar customizations,
        which should be handled separately in the `status_bar_customization()` method.

        When overriding this method in a subclass, ensure that you call
        `super().local_overrides()` at the start of your method to preserve
        any configuration overrides defined by parent classes before applying
        additional customizations.
        """
        self.write(
            """
        #======================================================
        #
        #   Local overrides
        #
        #======================================================
        """
        )

    # ================================================================
    #
    #  If you prefer another edit key, call this inside your content()
    #
    #  It will be called after content and use the default edit_key
    #  if it has not already been called.
    #
    # ================================================================

    def edit_config(self, edit_key: str = "e") -> None:
        """Managing to first edit the right file then using it to
        generate a tmux config for the right tmux version, and finally
        sourcing it, requires a lot of special considerations,
        therefore this is a template for doing this.

        This is called without param after self.content() by this class.
        In order to give SubClasses a shot at changing the edit_key,
        it can be called within the content() method.
        If it has already been called, it will abort.

        Override with something else or an empty method if this is not
        desired.
        """
        if self.e_c_has_been_called:
            return
        self.e_c_has_been_called = True

        w = self.write
        w(
            f"""

        # ======================================================
        #
        #   Edit config     <prefix>  {edit_key}
        #
        #  Both Homebrew on linux & using an asdf tmux might deploy tmux
        #  outside the generic shell path, in such cases running tmux from a
        #  script inside an interactive session will fail to find the intended
        #  bin.
        #
        #  For this reason the tmux bin used when defining the config,
        #  and the config file is used here to ensure the intended
        #  tmux is being regenerated, and finally sourced.
        #
        # ======================================================
        """
        )

        #
        #  For now we trust the right python to be found in path
        #  If this is not the one with the tmux-conf lib installed
        #  things will fail. If that turns out to be an issue, I guess
        #  storing the "right" python in the conf file would be a solution.
        #
        py_bin = run_shell("command -v python3")

        w(
            f'bind -N "Edit local config files"  {edit_key}  '
            + 'new-window -n "$TMUX_BIN config" '
            + "\"/bin/sh -c '\\${EDITOR:-vi} "
            + "$TMUX_SOURCE && "
            + f"{py_bin} $TMUX_SOURCE -r $TMUX_CONF && sleep 1 && "
            + "$TMUX_BIN source $TMUX_CONF && "
            + '$TMUX_BIN display \\"$TMUX_CONF sourced\\"\'"'
        )
        w("\n")

    # ================================================================
    #
    #  Some general methods that might be useful
    #
    # ================================================================
    def vers_ok(self, vers) -> bool:
        return self.vers.is_ok(vers)  # type: ignore

    # ================================================================
    #
    #        Rest is mostly for internal usage
    #
    # ================================================================

    def run(self) -> None:
        w = self.write

        #
        #  Inform plugin handler if this is to be treated as a
        #  limited host, displaying progress as tpm is processed etc
        #
        self.plugins.set_limited_host(self.is_limited_host)

        self.write_enable(False)  # ensure config file is not written to during plugin scan
        if self.plugin_handler:
            self.plugins.scan(self.list_plugin_methods())
            if self.plugins_display == 3:
                self.write_enable(True)
            if self.plugins_display:
                self.plugins.display_info()

        if not self.replace_config:
            self.verify_replace()

        self.conf_file_header()

        self.content()
        #
        #  check the edit_config() header in this class for hints on
        #  how to override the edit key
        #
        self.edit_config()
        if self.plugin_handler and self.plugins.installed():
            w(
                """#======================================================
            #
            #   Plugins
            #
            # ======================================================\n"""
            )
            for line in self.plugins.parse():
                if isinstance(line, list):
                    for sub_line in line:
                        self.write(sub_line)
                else:
                    self.write(line)

        #
        #  Local overrides should happen as late as possible, but still _before_
        #  tpm is triggered, to make sure overrides get processed.
        #
        self.local_overrides()

        self.write(self.plugins.deploy_plugin_handler())
        self.write()  # group spacer

        #
        #  Should be called as late as possible, to be able to have
        #  gathered all the intended embedded scripts.
        #
        for line in self.es.content():
            self.write(line)

    def list_plugin_methods(self):  # -> list[Callable[[], list[str]]]:
        """Support for plugins.py, provides a list of all plugin_... methods"""
        plugin_mthds = []
        if self.plugin_handler:
            for item in dir(self):
                if item.find("plugin_") or item == "plugin_handler":
                    continue
                plugin_mthds.append(getattr(self, item))
        return plugin_mthds

    # ===============================================================
    #
    #   write tmux conf
    #
    # ===============================================================

    def write_enable(self, state: bool) -> None:
        self._write_enabled = state

    def write(
        self, cmd: Union[str, list[str], list[list[str]]] = "", eol: str = "\n"
    ) -> None:
        """Writes tmux cmds to config file

        Filters out -N "note" statements if not supported, so they can
        always be supplied, regardless of tmux version.

        Can handle single and multi line commands, prints LF as a suffix.
        """
        if not self._write_enabled:
            #
            #  Plugin scans might trigger writes, at that point ignore them
            #
            return

        if isinstance(cmd, list):
            for line in cmd:
                self.debug_log(f"><> [list line] {line}")
                self.write(line)
            return  # list has already been processed

        if isinstance(cmd, str) and cmd.find("\n") > -1:
            for multi_line in cmd.split("\n"):
                # self.debug_log(f"><> [multi_line] {multi_line}")
                self.write(multi_line)
            return  # lines have already been processed

        if not self._parsing_note and cmd.find("bind -N") > -1:
            #
            #  Returns a list of lines. If input contained a -N and notes
            #  are not supported by this tmux, the note is extracted and
            #  the following is returned.
            #  self.use_notes_as_comments = True
            #   - note as a comment
            #   - the remainder of the initial line
            #  self.use_notes_as_comments = False
            #   - the remainder of the initial line
            #
            self._parsing_note = True  # avoid recursion
            self.debug_log(f"><> [-N cmd] {cmd}")
            for line in self.filter_note(cmd.strip()):
                self.debug_log(f"><> [note filtered line] {line}")
                self.write(line)
            self.debug_log("><> [end of -N cmd]\n")
            self._parsing_note = False
            return  # lines have already been processed

        if self.use_embedded_scripts and (btick_unescaped(str(cmd))):
            raise SyntaxError(
                "Un-escaped back-ticks can not be present in "
                + "the generated config when\n"
                + "embedded_scripts are used!"
            )

        # self.debug_log(f"><> [single line] {cmd}")
        with open(self.conf_file, "a", encoding="utf-8") as f:
            l123 = cmd.strip()
            self.debug_log(l123)
            f.write(f"{l123}{eol}")  # use strip to get rid of indentions
            #  f.write(f"{cmd}{eol}")

    def filter_note(self, line: str):
        """Handles notes, if tmux notes are not supported by running tmux
        generates:
          - the note as a comment (if self.use_notes_as_comments is True)
          - the actual command without the note
        """

        if (
            not line
            or line[0] == "#"
            or line.find("-N") < 0
            or (self.vers_ok("3.1") and self.use_notes_as_comments)
        ):
            return [line]
        parts = line.split("-N")
        pre = parts[0].strip()
        post = parts[1].strip()
        if not post:
            # Probably an -N at end of line, so not related to a note
            return [pre]
        p0 = post[0]
        if p0 in {'"', "'"}:
            end_note = post[1:].find(p0)
            x = end_note + 1
            note = post[1:x]
            y = end_note + 2
            post = post[y:]
        else:  # single word note
            note_end = post.find(" ")
            note = post.split()[0]
            post = post[note_end:]

        while post.find("   ") == 0:
            post = post[1:]
        new_line = pre + post
        if self.use_notes_as_comments:
            return [f"# -N {note}", new_line]

        return [new_line]

    # ===============================================================
    #
    #   handle tmux config file
    #
    # ===============================================================

    def conf_file_header(self) -> None:
        """Creates the conf-file header & sets a few env variables about
        what tmux and config file is used, so that external commands
        know what to call if needed.
        """
        self.remove_conf_file()
        self.write_enable(True)

        print(f"Writing tmux {self.vers.get()} config to {self.conf_file}")

        w = self.write
        if self.use_embedded_scripts:
            w(
                """# : << EMBEDDED-SCRIPTS-STARTING-POINT
            #
            # The above line tells embedded scripts where they start
            # further down in this file"""
            )

        w(
            f"""#
        #  This config was created using
        #      https://github.com/jaclu/tmux-conf
        #
        #      Creation time: {datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")}
        #          tmux-conf: {self.lib_version}
        #         Created on: {run_shell("hostname").strip()}"""
        )
        if self.vers.get() != self.vers.get_actual():  # type: ignore
            w(f"#     actual version: ({self.vers.get_actual()})")
        w(f"#   For tmux version: {self.vers.get()}")  # type: ignore
        w(
            f"""#
        #
        #  Three env variables defining this instance of tmux:
        #

        #
        #  When you might use various tmux instances or tmux is not in
        #  path, the safe bet is to always use $TMUX_BIN in a shell, not tmux!
        #
        TMUX_BIN="{self.tmux_bin}"

        #
        #  Helper pointitng to what conf file defines this env
        #  If you want to source the config, especially if the config
        #  might not be in the default location do:
        #    $TMUX_BIN source $TMUX_CONF
        #
        TMUX_CONF="{self.conf_file}"

        #
        #  Since this is a compiled config file, please examine $TMUX_SOURCE
        #  for what generated this. That is the right place for any changes
        #  and to examine comments about what is generated and why.
        #  This .conf file will frequently be over-written!
        #
        TMUX_SOURCE="{__main__.__file__}"
        """
        )

    def verify_replace(self) -> None:
        """Get verification that a config should be over-written
        the param replace_config=True skips this check
        """
        default_conf_file = os.path.expanduser("~/.tmux.conf")
        if self.conf_file == default_conf_file:
            self.check_replace_default_config()
        elif os.path.exists(self.conf_file):
            self.check_replace_custom_config()

    def check_replace_default_config(self) -> None:
        if os.path.isfile(self.conf_file) or os.path.islink(self.conf_file):
            confirmation = input("Do you wish to replace the default config file (y/n)?")
        else:
            confirmation = input("Do you wish to create a default config file (y/n)?")
        if confirmation not in ("y", "Y"):
            print("Terminating...")
            sys.exit(1)

    def check_replace_custom_config(self) -> None:
        confirmation = input(f"Do you wish to replace {self.conf_file} (y/n)?")
        if confirmation not in ("y", "Y"):
            print("Terminating...")
            sys.exit(1)

    def remove_conf_file(self) -> None:
        if os.path.exists(self.conf_file):
            #  Ensure we start with an empty file
            os.remove(self.conf_file)

    # ===============================================================
    #
    #   identify tmux bin
    #
    # ===============================================================

    def find_tmux_bin(self, cmd: str = "tmux") -> str:
        """if tmux should use a specific version, when generating config
        set requested_vers parameter, if empty the actual version is used
        if found, will set self.tmux_bin and more
        if not Raises exception
        """
        if not cmd:
            cmd = self.find_cmd_prev_conf()

        if not cmd:
            #  tmux not found abort
            print("ERROR could not find tmux binary, aborting")
            sys.exit(1)
        return self.full_path_cmd(cmd)

    def find_cmd_prev_conf(self) -> str:
        """First check is to see if the tmux used to generate the
        previous config can be extracted.
        """
        cmd = ""
        if os.path.isfile(self.conf_file):
            s = f'grep "TMUX_BIN=" {self.conf_file} | cut -d= -f 2 | sed s/\\"//g'
            c = run_shell(s).strip()
            if not c:
                return ""
            c2 = shutil.which(c)  # try to expand full path if not given
            if not c2:
                return ""
            cmd = c2
            print(f"found {cmd} in conf file")
        return cmd

    def use_tmux_bin(self, tmux_bin: str = "tmux", requested_vers: str = "") -> bool:
        """Returns True if this was a valid tmux bin
        If this was the case self.tmux_bin & self.vers will have been set
        """
        if not tmux_bin:
            tmux_bin = self.find_tmux_bin()  # now a full path

        parts = run_shell(f"{tmux_bin} -V").split(" ")
        if len(parts) != 2 or parts[0] not in ("tmux", "tmate"):
            self.debug_log(f"><> [error] {tmux_bin} Doesn't seem to be a tmux binary")
            raise TmuxConfNotTmuxCommand(f"{tmux_bin} Doesn't seem to be a tmux binary")

        vers = VersionCheck(actual_vers=parts[1], requested_vers=requested_vers)
        # except TmuxConfInvalidTmuxVersion:
        #     print("{parts[[1]} Doesn't seem to be a valid tmux version")
        #     return False
        self.tmux_bin = tmux_bin
        # pylint: disable=W0201
        self.vers = vers
        return True

    def full_path_cmd(self, cmd: str = "tmux") -> str:
        # returns full path of cmd if found
        c = run_shell(f"command -v {cmd}")
        if c and c.lower().find("not found") > -1:
            raise TmuxConfNotTmuxCommand(f"Not found: {cmd}")
        if c.find(".asdf/shims") > -1:
            cmd = self.full_path_cmd(c)
        print(f"found {cmd} in PATH")
        return cmd

    def is_tmate(self) -> bool:
        return self.tmux_bin.find("tmate") > -1

    # ===============================================================
    #
    #   debug
    #
    # ===============================================================
    def init_debug_log(self):
        if not self.use_debug_log:
            return

        d_base = os.getenv("HOME") or os.getenv("TMPDIR")
        if d_base:
            self.debug_log_file = Path(d_base + "/tmux_conf-dbg.log")
        else:
            # Failed to find a base dir
            self.use_debug_log = False
            return
        if self.debug_log_file.exists():
            self.debug_log_file.unlink()

    def debug_log(self, msg):
        if self.use_debug_log:
            with open(self.debug_log_file, "a", encoding="utf-8") as f:
                f.write(f"{msg}\n")
