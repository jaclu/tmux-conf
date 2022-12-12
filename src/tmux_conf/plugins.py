#
#  Copyright (c) 2022: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#
#  Class that handles tmux plugins
#
#  See the README.md in the repository for more info
#

import os
import shutil
import sys
from collections.abc import Callable
from typing import Union

import __main__

from .constants import XDG_CONFIG_HOME
from .embedded_scripts import EmbeddedScripts
from .vers_check import VersionCheck

PLUGIN_VERS_MIN = 0
PLUGIN_MTHD = 1
PLUGIN_STATIC_CODE = 2


#
#  Tasks related to plugins, taken separately to keep files smaller
#
class Plugins:
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
        # self._used_plugins: dict[
        #     str, tuple[str, Callable[[], tuple[str, str, str]], str]
        # ] = {}  # plugins that will be used
        #: dict[
        #    str, tuple[str, classmethod, str]
        # ]
        self._skipped_plugins: list[
            tuple[str, str]
        ] = []  # plugins incompatible with this version
        self._fnc_activate_tpm = "activate_tpm"
        self._fnc_activate_manually = "activate_plugins_mamually"

        if plugins_display not in [0, 1, 2, 3]:
            raise ValueError("plugins_display must be one of: 0, 1, 2, 3")
        self._plugins_display = plugins_display
        if clear_plugins:
            #
            #  if plugins_display is set, it will terminate the app,
            #  so lets do this before
            #
            self.clear()

    def found(self, short_name=True):
        """Returns a list of plugin names being used.
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

    def get_deploy_dir(self) -> str:
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

    def scan(self, plugin_methods) -> None:
        """Investigate all defined plugin methods, and determine if a
        given plugin can be used depending on running tmux"""
        duplicate_check = []
        for plugin_mthd in plugin_methods:
            plugin_name, vers_min, code = plugin_mthd()
            if plugin_name in duplicate_check:
                print(f'ERROR: plugin "{plugin_name}" defined more than once:')
                sys.exit(1)
            else:
                duplicate_check.append(plugin_name)
            #  Since plugi method might define vers_min as a float
            #  we need to convert it to a string both for used and ignored plugins
            if self._vers.is_ok(vers_min):
                self._used_plugins[plugin_name] = (
                    str(vers_min),  # self.PLUGIN_VERS_MIN
                    plugin_mthd,  # self.PLUGIN_MTHD
                    code,  # self.PLUGIN_STATIC_CODE
                )
            else:
                self._skipped_plugins.append((str(vers_min), plugin_name))
        self._skipped_plugins.sort()

    def display_info(self):
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
            print(f'{"Plugin":<{max_l_name}}|  Min version\n')

        #
        #  Create list of items in plugins dir
        #
        # plugin_items = next(os.walk(self.get_deploy_dir()))[1]
        plugin_items = []
        plugin_dir = self.get_deploy_dir()
        if os.path.exists(plugin_dir):
            for f in os.scandir(plugin_dir):
                if f.is_dir():
                    plugin_items.append((f.path.split("/")[-1]))

        if "tpm" in plugin_items:
            plugin_items.remove("tpm")
        #
        #  When exec'ing the plugin code below, write output to stdout,
        #  not to config file. Since program will exit after displaying
        #  plugin details, no need to reset this variable.
        #
        verbose = self._plugins_display == 3

        missing_plugins = []
        for name, info in self._used_plugins.items():
            if verbose:
                sans_prefix = name.split("/")[1]
                if sans_prefix in plugin_items:
                    plugin_items.remove(sans_prefix)
                    suffix = ""
                else:
                    suffix = " *** Not installed ***"
                print("".ljust(len(name) + 2, "-"))
                print(f"> {name:<{max_l_name - 2}} - {info[PLUGIN_VERS_MIN]} {suffix}")
                info[PLUGIN_MTHD]()
                #
                #  Skip indention, for easier read
                #
                for line in info[PLUGIN_STATIC_CODE].split("\n"):
                    # if line == line.strip():
                    print(f"{line.strip()}")
                # print()
            else:
                sans_prefix = name.split("/")[1]
                if sans_prefix in plugin_items:
                    plugin_items.remove(sans_prefix)
                    suffix = ""
                else:
                    suffix = " *** Not installed ***"
                print(f"{name:<{max_l_name}} - {info[PLUGIN_VERS_MIN]} {suffix}")

        for _, name in self._skipped_plugins:
            if name.find("/") > -1:
                sans_prefix = name.split("/")[1]
            else:
                sans_prefix = name
            if sans_prefix in plugin_items:
                plugin_items.remove(sans_prefix)

        if plugin_items:
            print("\n-----   Unused plugins found   -----")
            for s in plugin_items:
                print("\t", s)

        if not self._skipped_plugins or self._plugins_display != 2:
            sys.exit(0)

        if self._skipped_plugins:
            print()

        max_l_v = 0
        self._skipped_plugins.sort()
        for vers, name in self._skipped_plugins:
            max_l_v = max(max_l_v, len(vers))
        print("-----   Plugins ignored   -----")
        print(f'{"Min":<{max_l_v}}|{" Plugin name":<{max_l_name}}')
        print(f'{"vers":<{max_l_v}}|\n')
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
        if not (self._used_plugins):
            return []

        output: list[Union[str, list[str]]] = []

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
            output.append(f'set -g @plugin "{name}"')
            for line in info[2].split("\n"):
                output.append(line.strip())

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
        output.append("")  # spacer between sections
        return output

    def get_env(self):
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
            # pylint: disable=consider-using-assignment-expr
            if xdg_home:
                conf_base = os.path.expanduser(xdg_home)
            else:
                conf_base = os.path.dirname(location)

            if not conf_base:
                raise SyntaxError(
                    f"conf_base could not be extracted [{xdg_home}] "
                    + "[tilde_home_dir({self._conf_file})]"
                )

            plugins_dir = os.path.join(conf_base, "tmux", "plugins")
            if conf_base:
                tpm_env = f'XDG_CONFIG_HOME="{conf_base}" '
            else:
                tpm_env = ""
        if plugins_dir[0] not in ("/", "~"):  # TODO: Not windows compatible
            plugins_dir = os.path.join(os.getcwd(), plugins_dir)

        if tpm_env.find("~") > -1:
            raise SyntaxError(
                "XDG_CONFIG_HOME can not contain ~ "
                + "tpm does not bother with expanduser :("
            )
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
        for p in self.found(short_name=False):
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
        init_script="$(find "{plugins_dir}/$name" -maxdepth 1 | grep tmux$ | head -n 1)"
        if [[ -n "$init_script" ]]; then
            $TMUX_BIN display "running: $init_script"
            $init_script || echo "ERROR in $init_script"
        fi
    done
}}""",
        ]
        self._es.create(
            self._fnc_activate_manually, activate_manually_sh, use_bash=True
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

        run_installed_tpm = f"{tpm_env}{tpm_app}"
        if self._is_limited_host:
            run_installed_tpm = f"""#
        #  If you quickly shut down tmux whilst tpm is still running, things
        #  can go wrong. On all normal systems, this is so instantaneous,
        #  that it is not an issue, but on slow systems, this can take
        #  a noticeable time, up to five seconds when running iSH for example,
        #  so in such cases try to wait to exit until after "tpm completed!"
        #  has been announced.
        #
        $TMUX_BIN display "Running tpm..."
        {run_installed_tpm}
        $TMUX_BIN display "tpm completed!" """

        activate_tpm_sh = [
            f"""
{self._fnc_activate_tpm}() {{
    #
    #  Initialize already installed tpm if found
    #
    if [ -x "{tpm_app}" ]; then
        {run_installed_tpm}
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
        self._es.create(self._fnc_activate_tpm, activate_tpm_sh)
        return output

    def clear(self):
        """To minimize risk of some bug causing massive file deletion,
        file path is double checked.
        """
        plugins_dir = self.get_deploy_dir()

        b_suspicious = False
        if "tmux/" not in plugins_dir:
            b_suspicious = True
        elif plugins_dir in ("", "/", os.path.expanduser("~")):
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
            try:
                shutil.rmtree(path)
            except OSError:
                os.remove(path)
