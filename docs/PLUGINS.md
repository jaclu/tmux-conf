# Plugins

Methods starting with `plugin_` define plugins. They return:

1. Name of plugin to be installed
1. minimum tmux version for this plugin. Normally if tmux vers is lover than
the minimum version, this plugin will be listed as ignored.
To completely skip a plugin, use min version: -1.
1. tmux code snippet handling assignments of plugin variables etc

Any method starting with plugin\_ will be assumed to be a plugin
definition, and handled as such by the TmuxConfig class.

## Plugin usage order

Plugins will be placed in tmux.conf in alphabetical order based on method name.

Normally the order does not matter, but if there is a corner case
renaming the plugin method is enough to change the order.
For example tmux-continuum stated a while back that their plugin
should be last or at least as late as possible

```python

    def plugin_zz_continuum(self) -> list:  # 1.9
        """Automatically save and restore tmux server's open sessions.

        Depends on the plugin tmux-resurrect for actual save/restore.

        Due to a "known issue" mentioned on the plugins GitHub page, this
        plugin method name is intended to make sure this is the last
        plugin defined. Here is this issue:

        In order to be executed periodically, the plugin updates the
        status-right tmux variable. In case some plugin (usually themes)
        overwrites the status-right variable, the autosave feature stops
        working. To fix this issue, place the plugin last in the TPM plugins list.
        """
        conf = """
        set -g @continuum-save-interval  15
        set -g @continuum-restore        on
        """
        return ["tmux-plugins/tmux-continuum", 1.9, conf]


```

## Skipping a plugin

Normally if the running tmux doesnt match the min_version for a plugin,
it will be listed as an ignored plugin, and if it matches the plugin will be used.

If a config decides that a plugin should not be used at all, such as:

- a music player would be pointless to use on a cloud host
- if running on iSH or other environments with limited resources
- if a sub-class simply does not want to use this one

Setting `vers_min = -1`, means that this plugin will be entirely skipped,
and not listed as ignored.

-1.0 is also supported, since often when `vers_min` is used in an `if-else` clause,
the other option is a float.

In such cases using -1.0 ensures linters wont
complain about `"Incompatible types in assignment"`

### Skipping a plugin in a sub-class

If it is defined in a parent class, redefining it with a min version of -1
in a sub-class will result that this plugin is entirely skipped.

```python

    def plugin_packet_loss(self):
        """Dummy to override base class instance.
        The plugin name below has no significance for ignored plugins,
        it can be empty, but it might make sense to use a meaningful name.
        This will make it easy to see exactly what plugin was disabled."""
        return ["jaclu/tmux-packet-loss", -1, ""]

```

### Making a plugin definition context aware

I use two tmux envs, often running the secondary inside the outer.

For some plugins it wouldn't make sense to be used in an inner tmux.
Another concern could be that plugins might be resource intensive, thus
unsuitable for limited environments, or not usable for tmate etc.

For such plugins an env condition can be made, and if this plugin should
not be used in this case, setting `min_vers = -1.0` will skip it.

```python

    def plugin_session_wizard(self) -> list:
        if self.skip_plugin_session_wizard or (
            self.t2_env or self.is_ish or self.is_termux or self.is_tmate
        ):
            vers_min = -1.0  # Dont use
        else:
            vers_min = 3.2  # Actual min vers, checked vs running tmux
        return ["27medkamal/tmux-session-wizard", vers_min, ""]

```

## Really old tmux versions

tpm requires version 1.9, for older versions if a plugin handler is
defined, it is changed into manual. This makes pluguin handling possible
for any version of tmux.

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
