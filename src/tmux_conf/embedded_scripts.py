#  -*- mode: python; mode: fold -*-
#
#  Copyright (c) 2022: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#
#  Class that handles embedded scripts
#
#  See the README.md in the repository for more info
#

import os
import pathlib
import stat
import subprocess
import sys

from .constants import XDG_CONFIG_HOME
from .utils import tilde_home_dir


class EmbeddedScripts:
    """Handles scripts, either embedded or stored in scripts/ as external"""

    def __init__(self, conf_file: str, use_embedded_scripts: bool):

        #  Ensure conf file is using ~ or full path if ~ not applicable
        conf_file = tilde_home_dir(conf_file)
        if conf_file[0] not in ("~", "/"):
            conf_file = tilde_home_dir(os.path.join(os.getcwd(), conf_file))
        self._conf_file = conf_file

        self._use_embedded_scripts = use_embedded_scripts
        self._scripts: list[str] = []
        self._bash_scripts: list[str] = []
        self._bash_shell = ""  # Will only be set if needed

    def create(self, scr_name: str, script: list[str], use_bash: bool = False):
        """Creates a script, supplied as a list of lines
        script lines can be regular lines as string, or multi-line strings

        Where the script should be run, just call run_it() with
        the script name, and code will be generated to call it the right way.

        calling self.run_it('activate_tpm')  will insert code like:
          run "cut -c3- /home/jaclu/t2/tmux/tmux.conf | sh -s activate_tpm"
        or:
          run "/home/jaclu/t2/tmux/scripts/activate_tpm.sh"

        depending on self._use_embedded_scripts
        """
        if self._use_embedded_scripts:
            if use_bash:
                self._bash_scripts.append(scr_name)
            self._scripts += script
            self._scripts.append("")  # separator between scripts
        else:
            script_dir = self.get_dir()
            os.makedirs(script_dir, exist_ok=True)
            if use_bash:
                shebang = "#!/usr/bin/env bash"
            else:
                shebang = "#!/bin/sh"

            script.insert(0, f"{shebang}\n")
            script.append(scr_name)  # trigger it to run without a param

            fname = f"{script_dir}/{scr_name}.sh"
            with open(fname, "w", encoding="utf-8") as f:
                for line in script:
                    f.write(f"{line}\n")

            #  Make it run able
            f = pathlib.Path(fname)
            f.chmod(f.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def run_it(self, scr_name: str, in_bg: bool = False) -> str:
        """Generate the code to run an embedded/external script"""
        cmd = "run "
        if in_bg:
            cmd += "-b "
        cmd += '"'
        if self._use_embedded_scripts:
            cmd += f"cut -c3- {self._conf_file} | "
            if scr_name in self._bash_scripts:
                if not self._bash_shell:
                    self._bash_shell = (
                        subprocess.run(
                            ["which", "bash"],
                            stdout=subprocess.PIPE,
                            check=True,
                        )
                        .stdout.decode("utf-8")
                        .strip()
                    )
                    if not self._bash_shell:
                        sys.exit("Failed to find bash!")

                cmd += self._bash_shell
            else:
                cmd += "sh"
            cmd += f" -s {scr_name}"
        else:
            cmd += f"{self.get_dir()}/{scr_name}.sh"
        cmd += '"'
        return cmd

    def content(self) -> list[str]:
        """Generates the code for embedded scripts to be written to
        the conf file"""
        if not (self._use_embedded_scripts and self._scripts):
            return []

        output = [
            """
        #======================================================
        #
        # EMBEDDED-SCRIPTS-STARTING-POINT
        #
        """
        ]
        #
        #  Embedded scripts starts at column 3, insert extra indention on
        #  each line
        #
        for script_line in self._scripts:
            mutlilines = script_line.split("\n")
            if len(mutlilines) > 1:
                #
                #  Was multi-line string, remove first and last lines if empty
                #
                if not mutlilines[0]:
                    mutlilines.pop(0)
                if not mutlilines[-1]:
                    mutlilines.pop(-1)
                for line in mutlilines:
                    output.append(f"# {line}")
            else:
                output.append(f"# {script_line}")
        output.append('# "$@" #  This triggers the embedded script')
        return output

    def get_dir(self):
        """Retrieves the location where scripts should be saved"""
        if self._use_embedded_scripts:
            raise SyntaxError("get_dir() called when use_embedded_scripts is True")

        if tilde_home_dir(self._conf_file) == "~/.tmux.conf":
            scripts_dir = os.path.expanduser("~/.tmux/scripts")
        else:
            conf_file = os.path.expanduser(self._conf_file)
            if conf_file[0] != "/":  # TODO: Not windows compatible
                conf_file = os.path.join(os.getcwd(), conf_file)

            xdg_home = os.environ.get(XDG_CONFIG_HOME)
            # pylint: disable=consider-using-assignment-expr
            if xdg_home:
                conf_base = xdg_home
            else:
                conf_base = os.path.dirname(os.path.dirname(conf_file))

            scripts_dir = os.path.expanduser(os.path.join(conf_base, "tmux", "scripts"))
        return scripts_dir
