#
#  Copyright (c) 2022: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#
#  Class that generates a .tmux.conf
#
#  See the README.md in the repository for more info
#
#  All paths stored internally are done so with ~ expanded
#


import os
import shutil
import subprocess  # nosec
import sys
from collections.abc import Callable
from datetime import datetime

import __main__

from .constants import __version__
from .embedded_scripts import EmbeddedScripts
from .plugins import Plugins
from .utils import (
    btick_unescaped,
    expanduser_plus,
    is_executable,
    parse_cmdline,
    run_shell,
    verify_conf_file_usable,
)
from .vers_check import VersionCheck


class TmuxConfig:

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
    #  set it to '' if you do not want to use tpm at all.
    #
    plugin_handler = "tmux-plugins/tpm"

    #
    #  If true and tmux is < 3.1 thus not supporting -N bind notes
    #  this extracts the note and inserts it before the line as a comment.
    #  If false, the note is just discarded.
    #
    use_notes_as_comments = True

    #
    #  If false, scripts are saved in scripts/ inside the tmux conf dir
    #
    use_embedded_scripts = True

    #
    #  Indicates if this host is low on performance, don't enable
    #  demanding plugins etc, I use this on my iSH nodes.
    #  This must be set during __init__(). It is assumed to alreadt been
    #  set to the intended state when self.run() is done.
    #
    #  The only usage of this in this package is to propagate it to
    #  the plugin handler, indicating as plugins are installed and
    #  activated, since this might take a noticeable time on slowe nodes.
    #  It is also avaiable in derived plugin_ methods
    #
    #  Other usages of this is up to implementation classes
    #
    is_limited_host = False

    #
    #  Default binary, if non given
    #
    tmux_bin = "tmux"

    lib_version = __version__

    def __init__(
        self,
        parse_cmd_line: bool = True,
        #
        #  if parse_cmd_line is True all other parameters are ignored
        #
        conf_file: str = "~/.tmux.conf",  # where to store conf file
        tmux_bin: str = "tmux",
        tmux_version: str = "",
        replace_config: bool = False,  # replace config with no prompt
        clear_plugins: bool = False,  # remove all current plugins
        plugins_display: int = 0,  # Display info about plugins
        # then terminate
    ):
        if parse_cmd_line:
            args = parse_cmdline()
            conf_file = args.conf_file
            tmux_bin = args.tmux_bin
            tmux_version = args.forced_version
            replace_config = args.replace
            clear_plugins = args.clear_plugins
            plugins_display = args.plugins_display

        if not tmux_bin:
            # Use default for class
            tmux_bin = self.tmux_bin

        #  cant use self.is_tmate() at this point, since self.tmux_bin
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

        self.e_c_has_been_called = False
        self._write_stdout = False

        print(f"Processing: {__main__.__file__}")

        self.conf_file = verify_conf_file_usable(conf_file)

        #
        #  add the class to have the functionality needed during
        #  self.find_tmux_bin(), it will later be called again with
        #  the version details for the actually used version
        #
        self.define_tmux_vers()

        self.find_tmux_bin(tmux_bin)
        if tmux_version and (tmux_version != self.vers.get()):
            self.define_tmux_vers(tmux_version)
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

        self.es = EmbeddedScripts(self.conf_file, self.use_embedded_scripts)

        #
        #  If current tmux is too old to handle tpm plugins,
        #  disable plugins entirely
        #
        if not self.vers_ok("1.9"):
            self.plugin_handler = ""
            if plugins_display > 0:
                sys.exit(
                    "Versions < 1.9 does not support tpm, "
                    + "so plugin info can not be displayed"
                )
        self.plugins = Plugins(
            conf_file=self.conf_file,
            vers_class=self.vers,
            es_class=self.es,
            plugin_handler=self.plugin_handler,
            clear_plugins=clear_plugins,
            plugins_display=plugins_display,
        )
        self.write_enable(
            False
        )  # Allow plugin cheks to run without writung to conf file

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

        # cf = tilde_home_dir(self.conf_file)
        # w(
        #     f'bind -N "Edit local config files"  {edit_key}  '
        #     + 'new-window -n "$TMUX_BIN config" '
        #     + "\"/bin/sh -c '\\${EDITOR:-vi} "
        #     + f"{__main__.__file__} && "
        #     + f"{py_bin} {__main__.__file__} -r {self.conf_file} && sleep 1 && "
        #     + f"$TMUX_BIN source {self.conf_file} && "
        #     + f'$TMUX_BIN display \\"{self.conf_file} sourced\\"\'"'
        # )
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
        return self.vers.is_ok(vers)

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

        # if not (verbose := self.plugins_display == 3):
        #     #
        #     # App terminates at end of display_info(),
        #     # so can be left disabled
        #     #
        #     self._calling_class.write_enable(False)
        self._write_stdout = True  # Needs to be true during plugin init
        self.write_enable(False)
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

        if self.plugin_handler and self.plugins.found():
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
        #  Should be called as late as possible, to be able to have
        #  gathered all the intended embedded scripts.
        #
        for line in self.es.content():
            self.write(line)

    def list_plugin_methods(self):
        """Support for plugins.py, provides a list of all plugin_... methods"""
        plugin_mthds: list[Callable[[], list[str]]] = []
        if self.plugin_handler:
            for item in dir(self):
                if item.find("plugin_") or item == "plugin_handler":
                    continue
                plugin_mthds.append(getattr(self, item))
        return plugin_mthds

    def write_enable(self, state: bool):
        self._write_enabled = state

    def conf_file_header(self):
        """Creates the conf-file header & sets a few env variables about
        what tmux and config file is used, so that external commands
        know what to call if needed.
        """
        self.remove_conf_file()
        self._write_stdout = False
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
        #      Creation time: {datetime.now().strftime("%y-%m-%d %H:%M:%S")}
        #          tmux-conf: {self.lib_version}
        #         Created on: {run_shell('hostname').strip()}
        #        Source file: {__main__.__file__}
        # """
        )
        if self.vers.get() != self.vers.get_actual():
            w(f"#     actual version: ({self.vers.get_actual()})")
        w(
            f"""#   For tmux version: {self.vers.get()}
        #
        #  Since this is a compiled config file, please examine $TMUX_SOURCE
        #  for what generated this. That is the right place for any changes
        #  and to examine comments about what is generated and why.
        #  This .conf file will frequently be over-written!
        #
        TMUX_SOURCE="{__main__.__file__}"

        #
        #  Helper pointitng to what conf file defines this env
        #
        TMUX_CONF="{self.conf_file}"

        #
        #  tpm and other apps can use this env variable to use the
        #  "right" tmux binary if you run multiple tmux versions.
        #
        TMUX_BIN="{self.tmux_bin}"
        """
        )

    def write(self, cmd: str = "", eol: str = "\n"):
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

        #
        #  Convert to lines actually to be written
        #
        lines: list[str] = []
        for raw_line in cmd.split("\n"):
            #
            #  Returns a list of lines. If input contained a -N and notes
            #  are not supported by this tmux, the note is extracted and
            #  the following is returned.
            #  self.use_notes_as_comments = True
            #   - empty string, vertical spacer
            #   - note as a comment
            #   - the remainder of the initial line
            #  self.use_notes_as_comments = False
            #   - the remainder of the initial line
            #
            for line in self.filter_note(raw_line.strip()):
                lines.append(line)

        if self._write_stdout:
            #
            #  Used for displaying plugin settings
            #
            for line in lines:
                print(line)
        else:
            with open(self.conf_file, "a", encoding="utf-8") as f:
                for line in lines:
                    if self.use_embedded_scripts and (btick_unescaped(line)):
                        raise SyntaxError(
                            "Un-escaped back-ticks can not be present in "
                            + "the generated config when\n"
                            + "embedded_scripts are used!"
                        )
                    f.write(f"{line}{eol}")

    def filter_note(self, line: str) -> list[str]:
        """Returns list of lines, if notes are not supported
        first an empty spacer line, then the note as a comment,
        and finally the actual command without the note
        if self.use_notes_as_comments is False
        only the third line from above is returned
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
        if (p0 := post[0]) in {'"', "'"}:
            end_note = post[1:].find(p0)
            x = end_note + 1
            note = post[1:x]
            y = end_note + 2
            post = post[y:]
        else:  # single word note
            note_end = post.find(" ")
            note = post.split()[0]
            post = post[note_end:]

        # pylint: disable=while-used,compare-to-zero
        while post.find("   ") == 0:
            post = post[1:]
        new_line = pre + post
        if self.use_notes_as_comments:
            return ["", f"#  {note}", new_line]

        return [new_line]

    #
    #  Should conf file be replaced?
    #
    def verify_replace(self):
        """Get verification that a config should be over-written
        the param replace_config=True skips this check
        """
        default_conf_file = os.path.expanduser("~/.tmux.conf")
        if self.conf_file == default_conf_file:
            self.check_replace_default_config()
        elif os.path.exists(self.conf_file):
            self.check_replace_custom_config()

    def check_replace_default_config(self):
        if os.path.isfile(self.conf_file) or os.path.islink(self.conf_file):
            confirmation = input(
                "Do you wish to replace the default config file (y/n)?"
            )
        else:
            confirmation = input("Do you wish to create a default config file (y/n)?")
        if confirmation not in ("y", "Y"):
            print("Terminating...")
            sys.exit(1)

    def check_replace_custom_config(self):
        confirmation = input(f"Do you wish to replace {self.conf_file} (y/n)?")
        if confirmation not in ("y", "Y"):
            print("Terminating...")
            sys.exit(1)

    #
    #  Selecting tmux bin
    #
    def use_tmux_bin(self, cmd: str):
        """Verify this is a valid tmux, and store its path & version

        self.tmux_bin   The tmux used
        self.tmux_vers  The version used

        """
        # Do a basic sanity check
        if self.is_tmux_bin(cmd):
            self.tmux_bin = cmd
            self.define_tmux_vers()
        else:
            print(f"ERROR: tmux bin seems invalid: {cmd}")
            sys.exit(1)

    def find_tmux_bin(self, cmd: str = "") -> bool:
        if not cmd:
            #  Use the first that gives something
            cmd = self.find_cmd_1() or self.find_cmd_2() or self.find_cmd_3()

        if cmd:
            # the asdf check needs to know what version this is
            self.use_tmux_bin(cmd)
        #
        #  asdf refers to bins via its shim dir, where versions cant be
        #  identified, since it depends on other ENV variables,
        #  in this case try to extract a full path to the tmux bin itself,
        #  but make sure not to expand an asdf path that has already
        #  been processed!
        #
        if cmd.find(".asdf") > -1 and cmd.find("/installs/") < 0:
            if not self.is_tmux_bin(cmd):
                print(f"ERROR: asdf tmux does not seem to be valid: {cmd}")
                sys.exit(1)
            cmd_asdf = (
                f'{cmd.split("shims/")[0]}installs/tmux/'
                f'{self.vers.get().split("-")[0]}/bin/tmux'
            )
            self.use_tmux_bin(cmd_asdf)

        if not cmd:
            #  tmux not found abort
            print("ERROR could not find tmux binary, aborting")
            sys.exit(1)
        return True

    def is_tmate(self):
        return self.tmux_bin.find("tmate") > -1

    def is_tmux_bin(self, cmd: str = "") -> bool:
        """Only checks if the requested bin seems to be a tmux or tmate,
        checking name and doing simplified version check, ie if
        the second part of version is int"""
        if not cmd:
            raise SyntaxError("cmd empty")
        if not (c := shutil.which(cmd)):
            raise SyntaxError(f"tmux cmd not found: {cmd}")
        cmd = c
        output = run_shell(f"{cmd} -V")
        name, v = output.split()
        if name not in ("tmux", "tmate"):
            return False
        i, _ = self.vers.get_sub_vers(v.split(".")[1])
        try:
            int(i)
        except ValueError:
            return False
        return True

    #  TODO: use a better name
    def define_tmux_vers(self, vers="", tmux_bin: str = "tmux"):
        if not tmux_bin:
            tmux_bin = self.tmux_bin
        vers_found = run_shell(f"{tmux_bin} -V | cut -d' ' -f2")

        self.vers = VersionCheck(vers_found, vers)

    #
    #  Various attempt at finding the tmux bin
    #
    def find_cmd_1(self):
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

    def find_cmd_2(self):
        """Next check PATH"""
        cmd = ""
        try:
            c = run_shell("command -v tmux")
        except subprocess.CalledProcessError:
            c = ""
        if c and c.lower().find("not found") < 0:
            cmd = c
            print(f"found {cmd} in PATH")
        return cmd

    def find_cmd_3(self):
        """Finally try some likely locations"""
        cmd = ""
        for c in (
            "/usr/local/bin",
            "/home/linuxbrew/.linuxbrew/bin/tmux",
            "~/.asdf/shims/tmux",
        ):
            c2 = expanduser_plus(c)
            if is_executable(c2):
                cmd = c2
                break
        return cmd

    def remove_conf_file(self):
        if os.path.exists(self.conf_file):
            #  Ensure we start with an empty file
            os.remove(self.conf_file)
