#
#  Copyright (c) 2022-2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#
#  See the README.md in the repository for more info
#

"""Class that handles tmux plugins"""

import os
import shutil

# pylint: disable=import-error
from collections.abc import Callable
from dataclasses import dataclass

from ..embeded_scripts import EmbeddedScripts
from ..vers_check import VersionCheck
from .deployment import PluginDeployment
from .display import PluginDisplay
from .registry import PluginRegistry


@dataclass
class Plugin:
    """Handles tmux plugins"""

    vers_min: str
    plug_def: Callable[[bool], bool]
    code: str


#
#  Main plugin coordinator - delegates to specialized classes
#
class Plugins:
    """Class that handles tmux plugins

    Normally if the running tmux doesn't match the min_version for a plugin,
    it will be listed as an ignored plugin, and if it matches
    the plugin will be used.

    If a config decides that a plugin should not be used at all, such as:

    - a music player would be pointless to use on a cloud host
    - if running on iSH or other environments with limited resources
    - if a sub-class simply does not want to use this one

    vers_min = -1
    Means that this plugin will be entirely skipped, and not listed as ignored.

    -1.0 is also supported, since often when `vers_min` is used in
    an `if-else` clause, the other option is a float.

    In such cases using -1.0 ensures linters won't
    complain about `"Incompatible types in assignment"`
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        conf_file: str,  # must use tilde for home dir
        vers_class: VersionCheck,
        es_class: EmbeddedScripts,
        plugin_handler: str = "tmux-plugins/tpm",
        clear_plugins: bool = False,
        plugins_display: int = 0,
    ):
        self._conf_file = conf_file
        self._is_limited_host = False

        # Initialize the specialized components
        self._registry = PluginRegistry(conf_file=conf_file, vers_class=vers_class)
        self._deployment = PluginDeployment(
            registry=self._registry, es_class=es_class, plugin_handler=plugin_handler
        )
        self._display = PluginDisplay(
            registry=self._registry, plugins_display=plugins_display
        )

        if clear_plugins:
            #
            #  if plugins_display is set, it will terminate the app,
            #  so lets do this before
            #
            self.clear()

    # ================================================================
    #
    #   Public API - delegates to specialized components
    #
    # ================================================================

    def installed(self, short_name: bool = True) -> list[str]:
        """Returns a list of plugin names being installed.
        This excludes defined but not already installed plugins.
        Purpose is when defining the status bars, in order not to define
        entries for absent plugins

        Returns a list of plugin names being used.
        If short_name is False will return the full name including
        source, this is needed when cloning the repo, but less desired
        when just checking if a given plugin is used in most cases.
        Since if a different fork of it is being used, the name would
        not match."""
        return self._registry.installed(short_name=short_name)

    def get_plugin_dir(self) -> str:
        """Returns dir where plugins will be installed."""
        return self._registry.get_plugin_dir()

    def get_env(self) -> tuple[str, str]:
        """Get plugin directory and TPM environment."""
        return self._registry.get_env()

    def set_limited_host(self, is_limited: bool) -> bool:
        """For this module, this indicates that the host is considered
        slowish, so extended status updates should be provided during
        plugin init, to help indicating when all the plugins are setup.
        On normalish system, this is close to instantaneous, so step by
        step progress is not really meaningful.
        """
        self._is_limited_host = is_limited
        return self._is_limited_host

    def scan(self, plugin_methods: list[Callable[[], list[str]]]) -> None:
        """Investigate all defined plugin methods, and determine if a
        given plugin can be used depending on running tmux, or if it should be skipped
        """
        self._registry.scan(plugin_methods)

    def display_info(self) -> None:
        """List selected and ignored plugins, depending on param"""
        self._display.display_info()

    def parse(self) -> list[str]:
        """Generate plugin references and configuration."""
        return self._deployment.parse()

    def deploy_plugin_handler(self) -> list[str]:
        """Adds the plugin handler (if any desired)"""
        return self._deployment.deploy_plugin_handler()

    def clear(self) -> None:
        """To minimize risk of some bug causing massive file deletion,
        file path is double checked.
        """
        plugins_dir = self.get_plugin_dir()

        b_suspicious = False
        if "tmux/" not in plugins_dir:
            b_suspicious = True

        if b_suspicious:
            raise FileNotFoundError(
                "Refusing to clear plugins due to suspicious "
                + f"plugin dir: [{plugins_dir}]"
            )

        if not os.path.exists(plugins_dir):
            return  # nothing to clear

        for file_name in os.listdir(plugins_dir):
            path = os.path.join(plugins_dir, file_name)
            print(f"removing plugin {file_name}")
            shutil.rmtree(path)
