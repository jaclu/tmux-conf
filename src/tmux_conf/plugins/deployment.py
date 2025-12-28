#
#  Copyright (c) 2022-2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#

"""Plugin deployment handling for tmux plugins"""

import os
from collections.abc import Callable

from ..embeded_scripts import EmbeddedScripts
from ..vers_check import VersionCheck
from .registry import PLUGIN_MTHD, PLUGIN_STATIC_CODE, PluginRegistry


class PluginDeployment:
    """Handles plugin deployment via TPM or manual installation.

    Handles:
    - Creating TPM deployment scripts
    - Creating manual deployment scripts
    - Generating plugin references and settings
    """

    def __init__(
        self,
        registry: PluginRegistry,
        es_class: EmbeddedScripts,
        plugin_handler: str = "tmux-plugins/tpm",
    ):
        self._registry = registry
        self._es = es_class
        self._plugin_handler = plugin_handler

        self._fnc_activate_tpm = "activate_tpm"
        self._fnc_activate_manually = "activate_plugins_manually"

    def parse(self) -> list[str]:
        """Generate plugin references and configuration.

        This method will use any plugin defining methods it can find.
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
        """
        used_plugins: dict[str, tuple[str, Callable[[], list[str]], str]] = (
            self._registry.get_used_plugins()
        )
        if not used_plugins:
            return []

        output = []
        vers: VersionCheck = self._registry.get_version_checker()

        #
        #  First ensure that plugin code that needs to process the
        #  environment is done and output is written to config.
        #
        for name, info in used_plugins.items():
            plugin_method = info[PLUGIN_MTHD]
            plugin_method()  # type: ignore[operator]

        # Callable[[], list[str]]
        #  Add plugin references and hard coded plugin settings.
        #
        for name, info in used_plugins.items():
            output.append("#------------------------------")
            if vers.is_ok("1.8"):
                output.append(f'set -g @plugin "{name}"')
                static_code = info[PLUGIN_STATIC_CODE]
                for line in static_code.split("\n"):  # type: ignore[union-attr]
                    output.append(line.strip())
            else:
                #  prior to 1.8, any variables starting with @ would get tmux
                #  stuck parsing the config file, so plugins without any such
                #  setting could be handled by activate_plugins_manually()
                #  This is such a rare edge case that it is not worth handling
                output += [
                    f"# plugin: {name}",
                    "# in versions < 1.8 @variables can not be used",
                    "",
                ]

        return output

    def deploy_plugin_handler(self) -> list[str]:
        """Adds the plugin handler (if any desired)"""
        if not self._registry.has_plugins():
            return []

        output = []

        if self._plugin_handler == "manual":
            #
            #  Setup manual plugin handling, check for each listed
            #  plugin and install if missing
            #
            output.extend(self.mkscript_manual_deploy())
            output.append(self._es.run_it(self._fnc_activate_manually, in_bg=True))
        elif self._plugin_handler:
            #
            #  For any other _plugin_handler setting, assume it is tpm
            #  or a clone.
            #
            output.extend(self.mkscript_tpm_deploy())
            output.append(self._es.run_it(self._fnc_activate_tpm, in_bg=True))
        return output

    def mkscript_manual_deploy(self) -> list[str]:
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
        plugins_dir, _ = self._registry.get_env()
        plugins = ""
        for p in self._registry.installed(short_name=False):
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
        $TMUX_BIN display "Plugins initialized!"
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

    def mkscript_tpm_deploy(self) -> list[str]:
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
        plugins_dir, _ = self._registry.get_env()
        tpm_location = os.path.join(plugins_dir, "tpm")
        tpm_app = os.path.join(tpm_location, "tpm")
        activate_tpm_sh = [
            f"""
{self._fnc_activate_tpm}() {{
    #
    #  Initialize already installed tpm if found
    #
    if [ -x "{tpm_app}" ]; then
        "{tpm_app}"
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
    "{tpm_app}"
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
    "{tpm_location}/bindings/install_plugins"
    if [ "$?" -ne 0 ]; then
        echo "Failed to run: {tpm_location}/bindings/install_plugins"
        exit 12
    fi

    $TMUX_BIN display "Plugin setup completed"
}}""",
        ]
        self._es.create(self._fnc_activate_tpm, activate_tpm_sh, built_in=True)
        return output
