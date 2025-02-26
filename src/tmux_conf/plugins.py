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

"""Class that handles tmux plugins"""

import os
import shutil
import sys

# pylint: disable=import-error
from collections.abc import Callable
from dataclasses import dataclass

import __main__

from .constants import XDG_CONFIG_HOME
from .embedded_scripts import EmbeddedScripts
from .vers_check import VersionCheck

PLUGIN_VERS_MIN = 0
PLUGIN_MTHD = 1
PLUGIN_STATIC_CODE = 2


@dataclass
class Plugin:
    """Handles tmux plugins"""

    vers_min: str
    plug_def: Callable[[bool], bool]
    code: str


#
#  Tasks related to plugins, taken separately to keep files smaller
#
# pylint: disable=too-many-instance-attributes
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
        self._vers = vers_class
        self._es = es_class
        self._plugin_handler = plugin_handler

        self._is_limited_host = False

        self._used_plugins: dict[str, tuple[str, Callable[[], list[str]], str]] = {}

        # plugins incompatible with this version
        self._skipped_plugins: list[tuple[str, str]] = []

        self._fnc_activate_tpm = "activate_tpm"
        self._fnc_activate_manually = "activate_plugins_manually"

        if plugins_display not in [0, 1, 2, 3]:
            raise ValueError("plugins_display must be one of: 0, 1, 2, 3")
        self._plugins_display = plugins_display
        if clear_plugins:
            #
            #  if plugins_display is set, it will terminate the app,
            #  so lets do this before
            #
            self.clear()

    # def defined(self, short_name: bool = True):
    #     """Returns a list of plugin names being defined.
    #     This also includes defined but not installed plugins.
    #     """
    #     return

    def installed(self, short_name: bool = True):
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

    # ================================================================
    #
    #        Rest is mostly for internal usage
    #
    # ================================================================

    def set_limited_host(self, is_limited: bool) -> bool:
        """For this module, this indicates that the host is considered
        slowish, so extended status updates should be provided during
        plugin init, to help indicating when all the plugins are setup.
        Om normalish system, this is close to instantaneous, so step by
        step progress is not really meaningful.
        """
        self._is_limited_host = is_limited
        return self._is_limited_host

    def scan(self, plugin_methods):  # list[Callable[[], list[str]]]) -> None:
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

    # pylint: disable=too-many-branches
    def display_info(self) -> str:
        """List selected and ignored plugins, depending on param"""
        print(f"\n\t=====  tmux {self._vers.get()} - Plugins defined  =====")
        print(f" for: {__main__.__file__}")

        #
        #  First loop to find longest plugin name
        #
        max_l_name = 0
        for name in self._used_plugins:
            max_l_name = max(max_l_name, len(name) + 2)

        if self._used_plugins:
            print("\n\t-----   Plugins used   -----")
            print(f"{'Plugin':<{max_l_name}}|  Min version")

        #
        #  Create list of items in plugins dir
        #
        # plugin_items = next(os.walk(self.get_plugin_dir()))[1]
        plugin_items = []
        plugin_dir = self.get_plugin_dir()
        if os.path.exists(plugin_dir):
            for f in os.scandir(plugin_dir):
                if f.is_dir():
                    plugin_items.append((f.path.split("/")[-1]))
        _ = self._remove_if_found(plugin_items, "tpm")

        #
        #  When exec'ing the plugin code below, write output to stdout,
        #  not to config file. Since program will exit after displaying
        #  plugin details, no need to reset this variable.
        #
        verbose = self._plugins_display == 3

        for name, info in self._used_plugins.items():
            if verbose:
                inner_name = self._name_sans_prefix(name)
                suffix = self._remove_if_found(
                    plugin_items, inner_name, " *** Not installed ***"
                )
                print("".ljust(len(inner_name) + 2, "-"))
                print(
                    f"> {inner_name:<{max_l_name - 2}} - {info[PLUGIN_VERS_MIN]} {suffix}"
                )
                info[1]()  # PLUGIN_MTHD
                #
                #  Skip indentation, for easier read
                #
                for line in info[2].split("\n"):  # PLUGIN_STATIC_CODE
                    # if line == line.strip():
                    print(f"{line.strip()}")
                # print()
            else:
                inner_name = self._name_sans_prefix(name)
                suffix = self._remove_if_found(
                    plugin_items, inner_name, " *** Not installed ***"
                )
                print(f"{inner_name:<{max_l_name}} - {info[PLUGIN_VERS_MIN]} {suffix}")

        #  Remove skipped plugins from plugin_items
        for _, name in self._skipped_plugins:
            inner_name = self._name_sans_prefix(name)
            _ = self._remove_if_found(plugin_items, inner_name)

        if plugin_items:
            print("\n-----   Unused plugins found   -----")
            for s in plugin_items:
                print("\t", s)

        if not self._skipped_plugins or self._plugins_display != 2:
            sys.exit(0)

        if self._skipped_plugins:
            print()

        #
        #  List all plugins installed, but not used
        #
        max_l_v = 0
        self._skipped_plugins.sort()
        for vers, name in self._skipped_plugins:
            max_l_v = max(max_l_v, len(vers))
        print("-----   Plugins ignored   -----")
        print(f"{'Min':<{max_l_v}}|{' Plugin name':<{max_l_name}}")
        print(f"{'vers':<{max_l_v}}|\n")
        for vers, name in self._skipped_plugins:
            print(f"{vers:>{max_l_v}}  {name:<{max_l_name}}")

        sys.exit(0)

    def parse(self):
        """This package will use any plugin defining methods it can find.
        They will be sorted alphabetically by method name, normally the order
        of plugins do not matter, but if you do want to force the sorting,
        just change the method name accordingly.

        They are assumed to start with plugin_ and have the following format:

        The method should return a triplet:
         min_version,
         plugin name - needed when installing it, and to identify it.
         code snippet defining plugin variables, can be empty string.

        The code snippet will just be copied as is, so if a version or other
        check is needed, put that code before the return. Within the method
        all normal tmux-conf functionality is available.

        Here are a few examples:
        """
        if not self._used_plugins:
            return []

        output = []

        #
        #  First ensure that plugin code that needs to process the
        #  environment is done and output is written to config.
        #
        for name, info in self._used_plugins.items():
            info[1]()

        #
        #  Add plugin references and hard coded plugin settings.
        #
        for name, info in self._used_plugins.items():
            output.append("#------------------------------")
            if self._vers.is_ok("1.8"):
                output.append(f'set -g @plugin "{name}"')
                for line in info[2].split("\n"):
                    output.append(line.strip())
            else:
                #  prior to 1.8, any variables starting wiith @ would get tmux
                #  stuck parsing the config file, so plugins without any such
                #  setting could be handled by activate_plugins_manually()
                #  This is such a rare edge case that it is not worh handling
                output += [
                    f"# plugin: {name}",
                    "# in versions < 1.8 @variables can not be used",
                    "",
                ]

        # output.append("")  # spacer between sections
        return output

    def deploy_plugin_handler(self):
        """Adds the plugin handler (if any desired)"""
        if not self._used_plugins:
            return []

        output = []

        if self._plugin_handler == "manual":
            #
            #  Setup manual plugin handling, check for each listed
            #  plugin and install if missing
            #
            output.append(self.mkscript_manual_deploy())
            output.append(self._es.run_it(self._fnc_activate_manually, in_bg=True))
        elif self._plugin_handler:
            #
            #  For any other _plugin_handler setting, assume it is tpm
            #  or a clone.
            #
            output.append(self.mkscript_tpm_deploy())
            output.append(self._es.run_it(self._fnc_activate_tpm, in_bg=True))
        return output

    def get_env(self) -> tuple[str, str]:
        """get environment"""
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
            tpm_env = os.path.expanduser(f'XDG_CONFIG_HOME="{conf_base}" ')

        return plugins_dir, tpm_env

    def mkscript_manual_deploy(self):
        """This script is run as tmux starts, all non-present
        plugins are installed, and an attempt is done to initialize
        each plugin.
        """
        output = []
        output.append(
            """
        #======================================================
        #
        #   Manual Plugin Handling
        #
        #======================================================
        """
        )
        plugins_dir, _ = self.get_env()
        plugins = ""
        for p in self.installed(short_name=False):
            plugins += " " + p

        activate_manually_sh = [
            f"""
#
#  This is a manual plugin handler, does not scan for items.
#  The plugins list must be altered manually
#
{self._fnc_activate_manually}() {{
    mkdir -p "{plugins_dir}"

    plugins=({plugins} )
    for plugin in "${{plugins[@]}}"; do
        name="$(echo "$plugin" | cut -d / -f2)"
        if [[ ! -d "{plugins_dir}/$name" ]]; then
            $TMUX_BIN display "cloning  $name"
            git clone "https://github.com/$plugin" "{plugins_dir}/$name"
        fi
        #  argh, handle softlinks to plugin folders, in order to find init...
        d_plugin_folder="$(realpath "{plugins_dir}/$name")"
        init_script="$(find "$d_plugin_folder" -maxdepth 1 | grep tmux$ | head -n 1)"
        if [[ -n "$init_script" ]]; then
            $TMUX_BIN display "running: $init_script"
            $init_script || $TMUX_BIN display "ERROR in $init_script"
        else
            $TMUX_BIN display "Could not find init for plugin: $name"
            sleep 2
        fi
    done
}}""",
        ]
        self._es.create(
            self._fnc_activate_manually,
            activate_manually_sh,
            use_bash=True,
            built_in=True,
        )
        return output

    def mkscript_tpm_deploy(self):
        """If tpm is present, it is started.
        If not, it is installed and requested to install all
        defined plugins.
        """
        output = []
        output.append(
            """
        #======================================================
        #
        #   Tmux Plugin Manager
        #
        #======================================================
        """
        )
        #  os.makedirs(plugins_dir, exist_ok=True)
        plugins_dir, tpm_env = self.get_env()
        tpm_location = os.path.join(plugins_dir, "tpm")
        tpm_app = os.path.join(tpm_location, "tpm")
        activate_tpm_sh = [
            f"""
{self._fnc_activate_tpm}() {{
    #
    #  Initialize already installed tpm if found
    #
    if [ -x "{tpm_app}" ]; then
        {tpm_env}{tpm_app}
        exit 0
    fi

    #  Create plugin dir if needed
    mkdir -p "{plugins_dir}"

    #  Remove potentially broken tpm install
    rm -rf "{tpm_location}"

    $TMUX_BIN display "Cloning {self._plugin_handler} into {tpm_location} ..."
    git clone https://github.com/{self._plugin_handler} "{tpm_location}"
    if [ "$?" -ne 0 ]; then
        echo "Failed to clone tmux plugin handler:"
        echo "  https://github.com/{self._plugin_handler}"
        exit 11
    fi

    $TMUX_BIN display "Running cloned tpm..."
    {tpm_env}"{tpm_app}"
    if [ "$?" -ne 0 ]; then
        echo "Failed to run: {tpm_app}"
        exit 12
    fi

    #
    #  this only triggers plugins install if tpm needed to be installed.
    #  Otherwise installing missing plugins is delegated to tpm.
    #  Default trigger is: <prefix> I
    #
    $TMUX_BIN display "Installing all plugins..."
    {tpm_env}"{tpm_location}/bindings/install_plugins"
    if [ "$?" -ne 0 ]; then
        echo "Failed to run: {tpm_location}/bindings/install_plugins"
        exit 12
    fi

    $TMUX_BIN display "Plugin setup completed"
}}""",
        ]
        self._es.create(self._fnc_activate_tpm, activate_tpm_sh, built_in=True)
        return output

    def clear(self):
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

    def _name_sans_prefix(self, name: str) -> str:
        if name.find("/") > -1:
            name = name.split("/")[1]
        return name

    def _remove_if_found(self, lst: list[str], item: str, warning: str = "") -> str:
        if item in lst:
            lst.remove(item)
            warning = ""
        return warning
