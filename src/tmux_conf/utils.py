#  -*- mode: python; mode: fold -*-
#
#  Copyright (c) 2022: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#
#  See the README.md in the repository for more info
#
#  All paths stored internally are done so with ~ expanded
#

import argparse
import os
import subprocess  # nosec B404

from .constants import __version__


def btick_unescaped(line: str) -> bool:
    """Ensure any back-ticks on the line are escaped,
    otherwise running embedded scripts will fail.
    """
    pos = line.find("`")
    if not line or pos < 0:
        return False  # None present
    if line[pos - 1] != "\\":
        return True  # Was nor escaped
    #
    # recurse to check rest of l§ine
    #
    resume_pos = pos + 1
    return btick_unescaped(line[resume_pos:])


def expanduser_plus(path: str) -> str:
    """Handles both ~ and $HOME"""
    return os.path.expanduser(os.path.expandvars(path))


def is_executable(cmd: str) -> bool:
    fpath = os.path.expanduser(cmd)
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def parse_cmdline():
    parser = argparse.ArgumentParser(
        description="This tmux conf compiler generates configs for tmux "
        + "versions 1.5 and up."
    )

    #  Prints tmux-conf version info then exits
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s using tmux-conf: {__version__}",
    )

    parser.add_argument(
        "-c",
        "--clear_plugins",
        action="store_true",
        help="Removes tpm and current plugins. "
        + "They will be reinstalled on next launch",
    )

    parser.add_argument(
        "-r",
        "--replace",
        action="store_true",
        help="Do not ask for confirmation before replacing a config file",
    )

    parser.add_argument(
        "-p",
        "--plugins_display",
        choices=[1, 2, 3],
        default=0,
        type=int,
        help="1=Used plugins 2=also ignored plugins 3=show config",
    )

    parser.add_argument(
        "-t", "--tmux_bin", help="Force usage of this tmux bin", default=""
    )

    parser.add_argument(
        "-V",
        "--forced-version",
        help="Hard-code tmux version to be assumed during process",
    )

    parser.add_argument(
        "conf_file",
        nargs="?",
        default="~/.tmux.conf",
        help="Config file to be created, Defaults to ~/.tmux.conf",
    )
    return parser.parse_args()


def run_shell(cmd: str) -> str:
    """Run a command in a shell"""
    # pylint: disable=subprocess-run-check
    result = subprocess.run(
        cmd, capture_output=True, text=True, shell=True  # nosec: B602
    )
    return result.stdout.strip()


def tilde_home_dir(path: str) -> str:
    """Converts full path to ~ notation
    Internally all path related variables are stored expanded for python
    readability. I try to allways use this when writing paths to the
    config file, to keep it generic"""
    path = os.path.expanduser(path)
    home_dir = os.path.expanduser("~")
    # pylint: disable=compare-to-zero
    if path.find(home_dir) == 0:
        r = path.replace(home_dir, "~")
    else:
        r = path
    return r


def verify_conf_file_usable(conf_file: str) -> str:
    """Verify conf_file can be written to"""
    if not conf_file:
        raise SyntaxError("ERROR: Empty conf_file param!")

    # FILES
    # ~/.tmux.conf
    # $XDG_CONFIG_HOME/tmux/tmux.conf
    # ~/.config/tmux/tmux.conf     Default tmux configuration file.
    # /usr/local/etc/tmux.conf     System-wide configuration file.

    #  Ensure it can be parsed by Python
    conf_file = expanduser_plus(conf_file)

    #  Ensure conf_file is referred to with full path
    if not os.path.dirname(conf_file):
        conf_file = os.path.join(os.getcwd(), conf_file)

    conf_location = os.path.dirname(conf_file)
    try:
        os.makedirs(conf_location, exist_ok=True)
    except PermissionError as error:
        print("ERROR: Could not create directory for config file!")
        raise PermissionError from error

    #  Ensure it can be written to
    # pylint: disable=too-many-try-statements
    try:
        with open(conf_file, "a", encoding="utf-8") as _:
            pass
    except IOError as error:
        print(f"ERROR: Could not write to config file: {conf_file}")
        raise IOError from error

    #  If it didn't exist, we just created an empty file, get rid of it
    if os.stat(conf_file).st_size < 1:
        os.remove(conf_file)

    #  Return full path notation for config file
    return conf_file
