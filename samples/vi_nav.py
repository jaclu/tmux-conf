#!/usr/bin/env python3
#
#  Copyright (c) 2022: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
"""Sample config, showing how to use settings depending on a recent
tmux version. And defining some plugins of various complexity

Also shows various methods to define plugins
"""

import sys

try:
    from tmux_conf import TmuxConfig
except ModuleNotFoundError:
    print("Dependency tmux_conf not installed!")
    sys.exit(1)


class ViNav(TmuxConfig):
    """Sample tmux.conf generator"""

    def content(self):
        """Generates the main content for the tmux.conf"""
        w = self.write  # short alias for write

        prefix_key = "C-w"
        w(f"set -g  prefix  {prefix_key}")
        w(f"bind    {prefix_key}  send-prefix")

        if self.vers_ok("3.2"):
            w("set -s  extended-keys on")
            #
            #  not needed for all terminal apps, but since it doesn't hurt,
            #  it makes sense to always include it
            #
            w("set -as terminal-features 'xterm*:extkeys'")

        #
        #  Only add item if dependent plugin is listed.
        #  This check only considers if the plugin is defined, not if
        #  it has actually been installed.
        #
        if "tmux-prefix-highlight" in self.plugins.installed():
            w("set -g  status-right '#{prefix_highlight}'")

        w(
            """
        # Pane navigate
        bind  -r h  select-pane -L
        bind  -r j  select-pane -D
        bind  -r k  select-pane -U
        bind  -r l  select-pane -R

        # Pane split
        bind  C-h  split-window -hb
        bind  C-j  split-window -v
        bind  C-k  split-window -vb
        bind  C-l  split-window -h

        # Pane resize
        bind -r  H  resize-pane -L
        bind -r  J  resize-pane -D
        bind -r  K  resize-pane -U
        bind -r  L  resize-pane -R
        """
        )

    def plugin_yank(self):
        """Uses plugin tmux-plugins/tmux-yank"""
        #
        # case 1: No settings for the plugin
        #
        return ["tmux-plugins/tmux-yank", 1.5, ""]

    def plugin_prefix_highlight(self):
        """Uses plugin tmux-plugins/tmux-prefix-highlight"""
        #
        #  case 2: Static options can just be returned
        #
        return [
            "tmux-plugins/tmux-prefix-highlight",
            1.8,
            """
            set -g @prefix_highlight_show_copy_mode  on
            set -g @prefix_highlight_copy_mode_attr  "fg=black,bg=yellow,bold"
            set -g @prefix_highlight_show_sync_mode  on
            set -g @prefix_highlight_sync_mode_attr "fg=black,bg=orange,blink,bold"
            """,
        ]

    def plugin_menus(self):
        """Uses plugin jaclu/tmux-menus"""
        #
        #  case 3: Dynamic options are defined inside the method.
        #
        conf = ""
        if self.vers_ok("3.2"):
            conf = """
            set -g @menus_location_x  C
            set -g @menus_location_y  C
            """
        return ["jaclu/tmux-menus", 3.0, conf]


if __name__ == "__main__":
    ViNav().run()
