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

"""Plugin display and reporting functionality"""

import os
import sys
from collections.abc import Callable

import __main__

from ..vers_check import VersionCheck
from .registry import PLUGIN_VERS_MIN, PluginRegistry


# pylint: disable=too-few-public-methods
class PluginDisplay:
    """Handles plugin display and reporting.

    Handles:
    - Displaying plugin information at various verbosity levels
    - Formatting plugin lists
    - Showing installed/skipped/unused plugins
    """

    def __init__(self, registry: PluginRegistry, plugins_display: int = 0):
        if plugins_display not in [0, 1, 2, 3]:
            raise ValueError("plugins_display must be one of: 0, 1, 2, 3")
        self._registry: PluginRegistry = registry
        self._plugins_display = plugins_display

    def display_info(self) -> None:
        """List selected and ignored plugins, depending on param"""
        used_plugins: dict[str, tuple[str, Callable[[], list[str]], str]] = (
            self._registry.get_used_plugins()
        )

        skipped_plugins: list[tuple[str, str]] = self._registry.get_skipped_plugins()
        self._print_header()
        max_l_name = self._calculate_max_name_length(used_plugins)
        plugin_items: list[str] = self._get_installed_plugin_items()

        self._display_used_plugins(used_plugins, plugin_items, max_l_name)
        self._display_unused_plugins(plugin_items, skipped_plugins)

        if skipped_plugins and self._plugins_display == 2:
            self._display_skipped_plugins(skipped_plugins, max_l_name)

        sys.exit(0)

    def _print_header(self) -> None:
        """Print the header with tmux version information."""
        vers: VersionCheck = self._registry.get_version_checker()
        print(f"\n\t=====  tmux {vers.get()} - Plugins defined  =====")
        print(f" for: {__main__.__file__}")

    def _calculate_max_name_length(
        self, used_plugins: dict[str, tuple[str, Callable[[], list[str]], str]]
    ) -> int:
        """Calculate the maximum plugin name length for formatting."""
        if not used_plugins:
            return 0
        return max(len(name) + 2 for name in used_plugins)

    def _get_installed_plugin_items(self) -> list[str]:
        """Get list of installed plugin directories, excluding tpm."""
        plugin_items = []
        plugin_dir = self._registry.get_plugin_dir()
        if os.path.exists(plugin_dir):
            for f in os.scandir(plugin_dir):
                if f.is_dir():
                    plugin_items.append(f.path.split("/")[-1])
        _ = self._remove_if_found(plugin_items, "tpm")
        return plugin_items

    def _display_used_plugins(
        self,
        used_plugins: dict[str, tuple[str, Callable[[], list[str]], str]],
        plugin_items: list[str],
        max_l_name: int,
    ) -> None:
        """Display all used plugins with their version requirements."""
        if not used_plugins:
            return

        print("\n\t-----   Plugins used   -----")
        print(f"{'Plugin':<{max_l_name}}|  Min version")

        verbose = self._plugins_display == 3
        name: str
        info: tuple[str, Callable[[], list[str]], str]
        for name, info in used_plugins.items():
            if verbose:
                self._display_plugin_verbose(name, info, plugin_items, max_l_name)
            else:
                self._display_plugin_brief(name, info, plugin_items, max_l_name)

    def _display_plugin_verbose(
        self,
        name: str,
        info: tuple[str, Callable[[], list[str]], str],
        plugin_items: list[str],
        max_l_name: int,
    ) -> None:
        """Display plugin information in verbose mode."""
        inner_name = self._registry.name_sans_prefix(name)
        suffix = self._remove_if_found(plugin_items, inner_name, " *** Not installed ***")
        print("".ljust(len(inner_name) + 2, "-"))
        print(f"> {inner_name:<{max_l_name - 2}} - {info[PLUGIN_VERS_MIN]} {suffix}")
        # print(f"><> {type(info[PLUGIN_MTHD])}")
        # sys.exit(1)
        info[1]()  # Execute plugin method for verbose output
        # Skip indentation, for easier read
        for line in info[2].split("\n"):
            print(f"{line.strip()}")

    def _display_plugin_brief(
        self,
        name: str,
        info: tuple[str, Callable[[], list[str]], str],
        plugin_items: list[str],
        max_l_name: int,
    ) -> None:
        """Display plugin information in brief mode."""
        inner_name = self._registry.name_sans_prefix(name)
        suffix = self._remove_if_found(plugin_items, inner_name, " *** Not installed ***")
        print(f"{inner_name:<{max_l_name}} - {info[PLUGIN_VERS_MIN]} {suffix}")

    def _display_unused_plugins(
        self, plugin_items: list[str], skipped_plugins: list[tuple[str, str]]
    ) -> None:
        """Display unused plugins found in the plugins directory."""
        # Remove skipped plugins from plugin_items
        for _, name in skipped_plugins:
            inner_name = self._registry.name_sans_prefix(name)
            _ = self._remove_if_found(plugin_items, inner_name)

        if plugin_items:
            print("\n-----   Unused plugins found   -----")
            for s in plugin_items:
                print("\t", s)

    def _display_skipped_plugins(
        self, skipped_plugins: list[tuple[str, str]], max_l_name: int
    ) -> None:
        """Display plugins that were skipped due to version requirements."""
        print()
        max_l_v = max(len(vers_val) for vers_val, _ in skipped_plugins)
        print("-----   Plugins ignored   -----")
        print(f"{'Min':<{max_l_v}}|{' Plugin name':<{max_l_name}}")
        print(f"{'vers':<{max_l_v}}|\n")
        for vers_val, name in skipped_plugins:
            print(f"{vers_val:>{max_l_v}}  {name:<{max_l_name}}")

    @staticmethod
    def _remove_if_found(lst: list[str], item: str, warning: str = "") -> str:
        """Remove item from list if found, return warning string if not found."""
        if item in lst:
            lst.remove(item)
            warning = ""
        return warning
