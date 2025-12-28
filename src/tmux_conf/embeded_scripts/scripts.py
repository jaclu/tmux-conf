#
#  Copyright (c) 2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/my_tmux_conf
#

"""
Handles Embedded scripts
"""

import os
from typing import Any

from ..utils import tilde_home_dir
from ..vers_check import VersionCheck
from .config import RunCmdConfig
from .emitter import ScriptEmitter
from .registry import ScriptRegistry
from .spec import ScriptSpec


class EmbeddedScripts:
    """High-level compatibility wrapper."""

    def __init__(
        self,
        conf_file: str,
        vers_class: VersionCheck,
        use_embedded_scripts: bool,
        plugin_handler: str,
    ) -> None:
        conf_file = tilde_home_dir(conf_file)
        if conf_file[0] not in ("~", "/"):
            # no leading path - assume conf_file name is relative to $HOME
            conf_file = tilde_home_dir(os.path.join(os.getcwd(), conf_file))

        self._cfg = RunCmdConfig(
            conf_file=conf_file,
            use_embedded=use_embedded_scripts,
            plugin_handler=plugin_handler,
            vers=vers_class,
        )
        self.registry = ScriptRegistry()

        self._emitter = ScriptEmitter(self._cfg)

    def create(
        self,
        scr_name: str,
        script_lines: list[str],
        use_bash: bool = False,
        built_in: bool = False,
    ) -> None:
        """Manual embedded handler forces bash"""
        if self._cfg.use_embedded and self._cfg.plugin_handler == "manual":
            # When embedded scripts are used in combination with manual plugin_handler,
            # since that script will be generated as bash, all other embedded scripts
            # also have to use bash, otherwise they risk failing to run as /bin/sh
            # barks at incompatible bashisms in the manual plugin handled
            use_bash = True

        spec = ScriptSpec(scr_name, script_lines, use_bash, built_in)

        if not self.registry.accept(spec):
            return

        self._emitter.emit(spec)

    def run_it(self, scr_name: str, in_bg: bool = False) -> str:
        """Generate run-it line"""
        spec = ScriptSpec(scr_name, [], False, False)  # dummy, only for name
        return self._emitter.run_cmd(spec, in_bg)

    def call_script(self, scr_name: str) -> str | Any:
        """For embedded scripts this is essentially another function in the tmux.conf"""
        if not self._cfg.use_embedded:
            return self._emitter.external_path(ScriptSpec(scr_name, [], False, False))
        return scr_name

    def generate_embedded_scripts_content(self) -> list[str]:
        """generate content"""
        return self._emitter.embedded_block()
