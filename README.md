# Tmux-Conf

This is meant for users running tmux on multiple hosts, not always
running the same version of tmux.

This generates tmux config files where version checks can be used, so
that features not working on a given version can be handled gracefully.
Either replaced by something suitable for that version, or just skipped.

This gets rid of annoying startup error messages for features not being
available on the running version and failure to parse the rest of the config.

The optional [plugin](docs/PLUGINS.md) handling is also automated in the
sense that plugins not usable on the given version of tmux are skipped.
If any plugins are defined they will be auto-installed on first run.

This in combination with hostname matching makes it easy to adopt a
given environment based both on tmux version available, and what
features are relevant for that host. Managing a music player is
probably not all that meaningful on a remote cloud host :)

The generation of a tmux.conf takes only a fraction of a second, so I
use some scripts to regenerate the config each time I start tmux on
that system.
This will make new features automatically activated as soon as that node
gets a tmux version supporting it, without having to give it any
thought.
I sometimes also bind keys for functionality not available on a given
version of tmux to display a message like "Popup scratchpad session
needs 3.2". So that I never have to wonder why nothing happened if I
attempt something not supported on that system.

## Availability

Simplest way to install is using `pip install tmux-conf`

## Suggested approach

Drop your current tmux.conf inside a content() method, wrapping stuff
to be written to the conf file inside write() statements. If you
experience version glitches, wrap those items inside vers_ok()
statements.

If so desired also migrating your current plugins setup into plugin_XX
methods. Thus they will also be version checked.

## General features

- First scans for plugins available for this version and creates a list
  of those plugins. This list can be used when defining the status line
  to only include parts relevant for plugins being used.
- Plugins are version checked, incompatible plugins are ignored.
- If tpm is used it will be installed if not present on startup.
- All version compatible plugins are installed on startup, regrdless
  if tpm or manual plugin handling is used.
- Check if the current tmux matches a version limit with vers_ok()
  to decide if something should be included.
- Conf file defines $TMUX_BIN, pointing to the actual tmux/tmate bin
  used to run this environment, and can be used in scripts and plugins
  to use the right binary.
- Built in script handling for tasks that would just be painful to
  mangle into tmux commands with all the escaping that entails.
  Scripts will either be embedded or stored in separate files.
- Filters out -N bind notes automatically if current tmux doesn't
  support the feature, so just leave them in if you prefer to use them.
- Lazy adopting, initially just drop in your current config.
  If at some point you experience a version complaining about something,
  just wrap that inside a vers_ok() clause and its done. No need to
  over-analyze your entire setup unless you experiment with older
  versions of tmux.
- Supports config inheritance, you can have your basic config,
  and then subclass it and define things like what plugins are being
  used on a per node basis.
- Platform dependent plugins can be auto filtered

## Conditional status bar snippets

Blindly including plugin related code in the status bar can lead to
issues, especially if the status bar snippet calls an external script.
If the script is not present, it will trigger an error, and if the
script is present, but that plugin isn't intended to be used at the
moment, it can lead to unintended side effects.

Recommended approach is to first check what plugins are currently used
by calling self.plugins.found().
This returns the names of all defined plugins matching the current tmux
version and can be used to only include relevant items in the
status bar.

```python

    w = self.write
    used_plugins = self.plugins.found()

    if "tmux-packet-loss" in used_plugins:
        sb_right = "#{packet_loss}" + sb_right

    if "tmux-prefix-highlight" in used_plugins:
        sb_right += "#{prefix_highlight}"

    w(f"set -g  status-right '{sb_right}'")

```

## Version Testing

Combining this with using for example asdf to build multiple versions
of tmux, this is a convenient way to test plugins you are working on
for version compatibility.
And if so desired a test bench to get your plugins to work with older
tmux versions.

## My usage case

In my case i have set it up with some basic plugins I normally always
expect to be available, then for my laptop I have added ones that
would only make sense on a local system, like that music player.
A few very limited systems have more resource heavy standard plugins
disabled automatically.

The end result is that I have one single tmux config I use on all
systems. You can check it out at
[jaclu/my_tmux_conf](https://github.com/jaclu/my_tmux_conf)
I don't have to think about what version of tmux is available, my
config takes care of adopting. When I start using a feature from a
new version of tmux, I can just put it in my standard config with a
version check preventing it from being used on older tmuxes.
As versions gets updated the new feature automatically becomes more
widely available.

## Version checks

Parameter for calls to vers_ok() is flexible, can be either int, float or
string. In most cases a float is sufficient, like 2.8

Since some versions include a trailing letter, like 3.3a, then a string
param would be needed. If version is given as int, it will be appended
with .0

## Example snippets

If you notice version glitches, start wrapping those inside conditions:

```python

    if self.vers_ok(3.2):
        w("set -s  extended-keys on")
        #
        #  Not needed for all terminal apps, but since it doesn't hurt,
        #  it makes sense to always include it
        #
        w("set -as terminal-features 'xterm*:extkeys'")

```

A more complex example, with multiple version considerations.
Since there is no real fall back option doing something similar for
older versions, if the running tmux is to old, a notice that the
feature is not available is bound to the key.

```python

    scrpad_key = "O"  # P being taken, this is pOpup :)
    if self.vers_ok(3.2):
        display_popup = "display-popup -h 70% -w 70% -E "
        if self.vers_ok(3.3):
            display_popup += "-T " '"#[align=centre] pOpup Scratchpad Session " '
        w(
            f'bind -N "pOpup scratchpad session"  {scrpad_key}  '
            f'{display_popup} "$TMUX_BIN -u new-session -ADs scratch"'
        )
    else:
        w(
            f'bind -N "pOpup not available warning"  {scrpad_key}  '
            f'display "pOpup scratchpad session needs 3.2"'
        )

```

## Scripting

This package handles using regular scripts for more complex tasks
that would just be painful to wrap inside tmux notation.

Such scripts can either be saved as embedded in the tmux conf file or
as external files in scripts/ next to plugins/

See [docs/scripting.md](docs/scripting.md) for more info.
