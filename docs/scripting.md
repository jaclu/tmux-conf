# Scripting

In principle full scripting can be embedded using tmux statements, but it
tends to be error prone and rather complex, so therefore support for
normal scripts is implemented. Either embeded or stored in separate
files.

src/tmux_conf/embedded_scripts.py handles scripting

## Defining scripts

Define the script by providing a script name and a list of script lines,
composed of either strings or multi-line strings to `self.es.create()`

```python
    #  to avoid typos I use constants for script names
    self.fnc_toggle_mouse = "toggle_mouse"

    # { and } must be escaped by doubling them
    toggle_mouse_sh = [
        f"""
{self.fnc_toggle_mouse}() {{
    #  This is so much easier to do in a proper script...
    old_state=$($TMUX_BIN show -gv mouse)
    if [ "$old_state" = "on" ]; then
        new_state="off"
    else
        new_state="on"
    fi
    $TMUX_BIN set -g mouse $new_state
    $TMUX_BIN display "mouse: $new_state"
}}"""
    ]
    self.es.create(self.fnc_toggle_mouse, toggle_mouse_sh)
```

The reason the script is expected to be a list of strings, is to make it
easier to add lines depending on conditionals.

## Calling scripts

In order to define when the script is run call self.es.run_it(script name),
this will insert a run statement, in this case bound to a key:

```python
    w(f"bind -N 'Toggle mouse on/off'  M  {self.es.run_it(self.fnc_toggle_mouse)}")
```

With `use_embedded_scripts = True` the script will be embedded in the
conf file and run thus:

```tmux
bind -N 'Toggle mouse on/off'  M  run "cut -c3- ~/.tmux.conf | sh -s toggle_mouse"
```

With `use_embedded_scripts = False` the script will be stored in scripts/
next to plugins/ and run thus:

```tmux
bind -N 'Toggle mouse on/off'  M  run "/Users/jaclu/.tmux/scripts/toggle_mouse.sh"
```

I prefer to use embedded scripts, this ensures that no out of date
scripts hang around in scripts/ and eliminates risk of scripts not found
if they are deleted, but either is valid so entirely up to you.

## Bash

Default is to generate /bin/sh style POSIX scripts. If bash functionality
is needed, self.es.create() has an optional param use_bash that can be
set to True

```python
    self.es.create(self.fnc_toggle_mouse, toggle_mouse_sh, use_bash=True)
```

This would generate the following (the correct path to bash is scanned
for):

```tmux
bind -N 'Toggle mouse on/off'  M  run "cut -c3- ~/.tmux.conf | /usr/local/bin/bash -s toggle_mouse"
```

For external scripts, the appropriate shebang defining what shell to use
will be set.

## Backticks

The main thing to be aware of is that if embedded scripts are used,
some considerations about handling backticks must be made.

Any un-escaped backticks in the conf file will cause embedded scripts to
fail. This is the case both for tmux code and comments.

Any backtick must use \\\` notation in the final conf file.
Not "\`" or '\`' otherwise the embedded script will fail to run,
reporting an error.

This means you have to double escape it in your Python code to ensure
the resulting tmux conf code is correctly escaped.

Probably the simplest thing to do is to just avoid using backticks. 
The number of attempts it took me to write this before I got all the escaping to 
generate the intended code was pure pain.

For external scripts there is no backtick issue with the tmux.conf file
