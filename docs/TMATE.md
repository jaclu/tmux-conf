# Tmate

This generates valid tmate configs, so by selecting tmate as the
desired binary by using `-t tmate`, you can generate a tmate compatible
config directly from your standard config.
This will assume version 2.4 for version checks and save the config to `~/.tmate.conf`
if no config file was specified on the command line.

There are some slight differences to what actually works with tmate
compared to tmux 2.4, the stated compatibility level, tmux-conf handles
those cases.

You can also check in your own code if the env being setup for tmate
by calling is_tmate()

Tpm is not compatible with tmate, so unless plugin_handler has been
disabled, it is switched to 'manual'. This works fine in combination
with tmate, including auto-install of plugins.

Be aware that most tmux plugins are not directly tmate compatible.
They tend to blindly run tmux. To fix that is pretty simple, replace
all references to tmux in the scripts of the plugin to instead use
$TMUX_BIN, this way it inherits what tmux bin to use (in this case tmate)
from the environment.

Even with that fix, sometimes they simply dont work under tmate,
even if they are suposed to be 2.4 compatible, so it is a bit hit-and-miss.

All that is needed to make the plugin usable without tmux-conf, is to add
this code snippet in the common script used to set up the environment,
often called `scripts/helpers.sh`, so that $TMUX_BIN is set in case
this plugin is used without a tmux-conf generated config.

```shell
#
#  I use an env var TMUX_BIN to point at the used tmux, defined in my
#  tmux.conf, in order to pick the version matching the server running,
#  or when the tmux bin is in fact tmate :)
#  If not found, it is set to whatever is in PATH, so should have no
#  negative impact. In all calls to tmux I use $TMUX_BIN instead in
#  the rest of this plugin.
#
[ -z "$TMUX_BIN" ] && TMUX_BIN="tmux"
```

Here are some plugins that work with tmate, in some cases I have adopted
them, with TMUX_BIN notation, then listing my fork.

plugin | fork
-|-
jaclu/tmux-keyboard-type|
NHDaly/tmux-better-mouse-mode | jaclu/tmux-better-mouse-mode
tmux-plugins/tmux-prefix-highlight  | jaclu/tmux-prefix-highlight
