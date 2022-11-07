# Plugins

Methods starting with `plugin_` define plugins. They return:

1. Name of plugin to be installed
1. minimum tmux version for this plugin
1. Assignments of plugin variables etc

Any method starting with plugin\_ will be assumed to be a plugin
definition, and handled as such by the TmuxConfig class.

Plugins will be ordered alphabetically based on method name.
Normally the order does not matter, but if there is a corner case
renaming the plugin method is enough to change the order.
For example tmux-continuum stated a while back that their plugin
should be last or at least as late as possible

```python

    def plugin_zz_continuum(self):

        #  2020-12-24
        #  ==========
        #  (From their repo) Due to a bug tmux-continuum should be as close
        #  to last plugin as possible to minimize the risk of a crucial tmux
        # variable `status-right` is not overwritten (usually by theme plugins).
        #
        return ["tmux-plugins/tmux-continuum",
        1.9,
        """
        set -g @continuum-restore        on
        set -g @continuum-save-interval  15
        """]

```

If not in one of the parent classes, just changing the name to something
like not_plugin_foo() is enough to ensure it is not used.

If it is defined in a parent class, redefining it with a ridiculously high min
version, will prevent that plugin from being used.

Since such a plugin will never be used, it does not need any meaningful content
in the third param, here is an example:

```python

def plugin_packet_loss(self):
    #  Dummy to override base class instance.
    #  The plugin name below has no significance for
    #  ignored plugins, it can be empty, but it might make sense
    #  to use a meaningful name. This will make you aware of what plugin was disabled.
    return ["jaclu/tmux-packet-loss", 99, ""]

```

## Sample config

This is taken from samples/vi_nav.py and displays the most important concepts.

```python

    def plugin_yank(self):
        #
        # case 1: No settings for the plugin
        #
        return ["tmux-plugins/tmux-yank", 1.9, ""]

    def plugin_prefix_highlight(self):
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
        #
        #  case 3: Dynamic options are defined inside the method.
        #
        conf = ""
        if self.vers_ok(3.2):
            conf = """
            set -g @menus_location_x  C
            set -g @menus_location_y  C
            """
        return ["jaclu/tmux-menus", 3.0, conf]

```
