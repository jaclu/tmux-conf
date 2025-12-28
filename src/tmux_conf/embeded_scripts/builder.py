#
#  Copyright (c) 2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/my_tmux_conf
#

"""
Defines a  run-shell to call a specific script
"""

import os
import sys
from typing import Any

from ..utils import run_shell
from .config import RunCmdConfig
from .spec import ScriptSpec


class CmdBuilder:  # pylint: disable=too-few-public-methods
    """Handles only the logic for building the tmux run-shell command."""

    def __init__(self, cfg: RunCmdConfig, external_resolver: Any) -> None:
        self.cfg: RunCmdConfig = cfg
        # For external scripts this is the full path script name
        # For embedded scripts, this is the name of the tmux.conf
        self._external_resolver = external_resolver

        self._cached_bash = ""

    def build(self, spec: ScriptSpec, in_bg: bool) -> str:
        """
        Docstring for build

        :param self: Description
        :param spec: Description
        :type spec: ScriptSpec
        :param in_bg: Description
        :type in_bg: bool
        :return: Description
        :rtype: str
        """

        cmd = "run-shell "
        if in_bg and self.cfg.vers.is_ok(1.8):
            cmd += "-b "
        cmd += '"'

        if self.cfg.use_embedded:
            cmd += f"cut -c3- '{os.path.expanduser(self.cfg.conf_file)}' | "
            if spec.use_bash:
                cmd += self._ensure_bash()
            else:
                cmd += "sh"
            cmd += f" -s {spec.name}"
        else:
            cmd += self._external_resolver(spec)

        cmd += '"'
        return cmd

    def _ensure_bash(self) -> str:
        if not self._cached_bash:
            detected_bash = run_shell("command -v bash")
            if not detected_bash:
                sys.exit("Failed to find bash!")
            self._cached_bash = detected_bash
        return self._cached_bash
