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

"""Plugin registry for managing tmux plugin collection"""

import os
import sys
from collections.abc import Callable

from ..constants import XDG_CONFIG_HOME
from ..vers_check import VersionCheck

PLUGIN_VERS_MIN = 0
PLUGIN_MTHD = 1
PLUGIN_STATIC_CODE = 2


class PluginRegistry:
    """Manages the collection of plugins and their metadata.

    Handles:
    - Plugin registration and scanning
    - Version compatibility checking
    - Plugin queries (installed, available, etc.)
    - Environment/directory management
    """

    def __init__(
        self,
        conf_file: str,
        vers_class: VersionCheck,
    ):
        self._conf_file = conf_file
        self._vers: VersionCheck = vers_class

        # plugins compatible with this version
        self._used_plugins: dict[str, tuple[str, Callable[[], list[str]], str]] = {}

        # plugins incompatible with this version
        self._skipped_plugins: list[tuple[str, str]] = []

    def scan(self, plugin_methods: list[Callable[[], list[str]]]) -> None:
        """Investigate all defined plugin methods, and determine if a
        given plugin can be used depending on running tmux, or if it should be skipped
        """
        duplicate_check = []
        for plugin_mthd in plugin_methods:
            plugin_name, vers_min, code = plugin_mthd()
            if plugin_name in duplicate_check:
                print(f'ERROR: plugin "{plugin_name}" defined more than once:')
                sys.exit(1)
            else:
                duplicate_check.append(plugin_name)
            #  Since plugin method might define vers_min as a float or int
            #  it needs to be converted to a string for plugin handling
            s_vers_min = str(vers_min)
            if s_vers_min in ("-1", "-1.0"):
                continue  # skip it entirely
            if self._vers.is_ok(s_vers_min):
                self._used_plugins[plugin_name] = (
                    s_vers_min,  # PLUGIN_VERS_MIN
                    plugin_mthd,  # PLUGIN_MTHD
                    code,  # PLUGIN_STATIC_CODE
                )
            else:
                self._skipped_plugins.append((s_vers_min, plugin_name))
        self._skipped_plugins.sort()

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
        result = []
        for full_name in self._used_plugins:
            name = full_name
            if short_name:
                # Try to return only actual plugin name, without provider
                if full_name.find("/") > -1:
                    name = full_name.split("/")[1]
            result.append(name)
        return result

    def get_plugin_dir(self) -> str:
        """Returns dir where plugins will be installed."""
        plugins_dir, _ = self.get_env()
        return plugins_dir

    def get_env(self) -> tuple[str, str]:
        """Get plugin directory and TPM environment."""
        location = os.path.dirname(os.path.expanduser(self._conf_file))
        if location == os.path.expanduser("~"):
            #
            #  If conf file is default, plugins have a non standard location
            #
            if self._conf_file.find("tmate") > -1:
                plugins_dir = os.path.expanduser("~/.tmate/plugins")
                tpm_env = ""
            else:
                plugins_dir = os.path.expanduser("~/.tmux/plugins")
                tpm_env = ""
        else:
            xdg_home = os.environ.get(XDG_CONFIG_HOME)
            if xdg_home:
                conf_base = os.path.expanduser(xdg_home)
            else:
                conf_base = os.path.dirname(location)

            plugins_dir = os.path.join(conf_base, "tmux", "plugins")
            tpm_env = f"{os.path.expanduser(conf_base)}"

        return plugins_dir, tpm_env

    def get_used_plugins(self) -> dict[str, tuple[str, Callable[[], list[str]], str]]:
        """Returns the dict of used plugins."""
        return self._used_plugins

    def get_skipped_plugins(self) -> list[tuple[str, str]]:
        """Returns the list of skipped plugins."""
        return self._skipped_plugins

    def has_plugins(self) -> bool:
        """Returns True if any plugins are registered."""
        return bool(self._used_plugins)

    def get_version_checker(self) -> VersionCheck:
        """Returns the version checker instance."""
        return self._vers

    @staticmethod
    def name_sans_prefix(name: str) -> str:
        """Remove provider prefix from plugin name."""
        if name.find("/") > -1:
            name = name.split("/")[1]
        return name
