#!/usr/bin/env python3
#
#  Copyright (c) 2022,2024: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  Copies files directly to user site-packages, should not be used
#  as a primary deploy method!
#
#  Mostly for iSH, when instlling a pip or building it locally
#  would take for ever.
#  This script tries to find a local site-packages, and then just
#  copy the relevant files there as is.
#
#  This should be run from the folderm where this is intended to be
#  used, it will find the site-packages in used there and manually
#  update that instance of tmux-conf

#  I also use this when testing new versions, in order not to have
#  to generate a local pip for every change.
#

import os
import shutil
import sys

import __main__

a = sys.path
a.reverse()

SP = "site-packages"

for p in sys.path[:-1]:
    if p.find(os.getenv("HOME") or "") < 0:
        continue
    if len(p) - len(SP) == p.rfind(SP):
        print(f"Checking {p}")
        # chdir to this location to make relative paths work
        os.chdir(os.path.dirname(__main__.__file__))

        DIR_SRC = "src/tmux_conf"
        DIR_DEST = f"{p}/tmux_conf"
        # os.remove(f'{DIR_DEST}*dist-info')
        if not os.path.isdir(DIR_DEST):
            print(f"ERROR: dir {DIR_DEST} does not exist!")
            sys.exit(1)
        shutil.copy(f"{DIR_SRC}/__init__.py", DIR_DEST)
        shutil.copy(f"{DIR_SRC}/constants.py", DIR_DEST)
        shutil.copy(f"{DIR_SRC}/embedded_scripts.py", DIR_DEST)
        shutil.copy(f"{DIR_SRC}/plugins.py", DIR_DEST)
        shutil.copy(f"{DIR_SRC}/tmux_conf.py", DIR_DEST)
        shutil.copy(f"{DIR_SRC}/utils.py", DIR_DEST)
        shutil.copy(f"{DIR_SRC}/vers_check.py", DIR_DEST)
        shutil.copy(f"{DIR_SRC}/exceptions.py", DIR_DEST)
        print(f"Copied tmux_conf files to user {DIR_DEST}")
        sys.exit(0)
    else:
        print(f"Skipping {p}")


print(f"ERROR: could not find a user {SP}!")
