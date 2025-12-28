#
#  Copyright (c) 2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/my_tmux_conf
#

"""
Docstring for tmux_conf.embeded_scripts.script_emitter
"""

import os
import pathlib
import stat
import sys

from ..utils import tilde_home_dir
from .builder import CmdBuilder
from .config import RunCmdConfig
from .spec import ScriptSpec


class ScriptEmitter:
    """
    Handles:
        - writing external scripts
        - building the embedded block for tmux.conf
        - directory resolution
        - passing correct paths to the Builder
    """

    def __init__(self, cfg: RunCmdConfig):
        self._builder = CmdBuilder(
            cfg=cfg,
            external_resolver=self.external_path,
        )
        self._embedded_text: list[str] = []

    def run_cmd(self, spec: ScriptSpec, in_bg: bool = False) -> str:
        """Generate a run-shell entry for the script"""
        return self._builder.build(spec, in_bg)

    def emit(self, spec: ScriptSpec) -> None:
        """Generate inline/external scripts"""
        if self._builder.cfg.use_embedded:
            self._emit_embedded(spec)
        else:
            self._emit_external(spec)

    def embedded_block(self) -> list[str]:
        """
        Docstring for embedded_block

        :param self: Description
        :return: Description
        :rtype: list[str]
        """
        if not (self._builder.cfg.use_embedded and self._embedded_text):
            return []

        out = [
            """
        #======================================================
        #
        # EMBEDDED-SCRIPTS-STARTING-POINT
        #"""
        ]
        out.extend(self._embedded_text)
        out.append('# "$@" #  This triggers the embedded script')
        return out

    def external_path(self, spec: ScriptSpec) -> str:
        """Proivdes external path"""
        return f"{self._script_dir()}/{spec.name}.sh"

    def _emit_embedded(self, spec: ScriptSpec) -> None:
        for line in spec.lines:
            # support multi-line chunks
            for part in line.split("\n"):
                self._embedded_text.append(f"# {part}")
        self._embedded_text.append("")  # separator

    def _emit_external(self, spec: ScriptSpec) -> None:
        script_dir = self._script_dir()
        try:
            os.makedirs(script_dir, exist_ok=True)
        except PermissionError:
            print(
                "EXCEPTION! PermissionError: _emit_external() Failed to create {script_dir}"
            )
            sys.exit(1)

        shebang = "#!/usr/bin/env bash" if spec.use_bash else "#!/bin/sh"

        txt = [f"{shebang}\n"]
        txt.extend(spec.lines)
        txt.append(f'{spec.name} "$@"')

        path = os.path.join(script_dir, f"{spec.name}.sh")

        try:
            with open(path, "w", encoding="utf-8") as f:
                for line in txt:
                    f.write(line.rstrip("\n") + "\n")
        except FileNotFoundError:
            print(f"EXCEPTION! FileNotFoundError: could not wrie to: {path}")
            sys.exit(1)
        p = pathlib.Path(path)
        p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _script_dir(self) -> str:
        if self._builder.cfg.use_embedded:
            raise SyntaxError("Embedded mode has no script directory")

        if tilde_home_dir(self._builder.cfg.conf_file) == "~/.tmux.conf":
            return os.path.expanduser("~/.tmux/scripts")

        if tilde_home_dir(self._builder.cfg.conf_file) == "~/.tmate.conf":
            return os.path.expanduser("~/.tmate/scripts")

        conf_file = os.path.expanduser(self._builder.cfg.conf_file)

        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            base = xdg
        else:
            base = os.path.dirname(os.path.dirname(conf_file))
        return os.path.join(base, "tmux", "scripts")
