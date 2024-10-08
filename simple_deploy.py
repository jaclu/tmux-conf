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
        dir_dest = f"{p}/tmux_conf"
        # os.remove(f'{dir_dest}*dist-info')
        if not os.path.isdir(dir_dest):
            print(f"ERROR: dir {dir_dest} does not exist!")
            sys.exit(1)
        shutil.copy(f"{DIR_SRC}/__init__.py", dir_dest)
        shutil.copy(f"{DIR_SRC}/constants.py", dir_dest)
        shutil.copy(f"{DIR_SRC}/embedded_scripts.py", dir_dest)
        shutil.copy(f"{DIR_SRC}/plugins.py", dir_dest)
        shutil.copy(f"{DIR_SRC}/tmux_conf.py", dir_dest)
        shutil.copy(f"{DIR_SRC}/utils.py", dir_dest)
        shutil.copy(f"{DIR_SRC}/vers_check.py", dir_dest)
        shutil.copy(f"{DIR_SRC}/exceptions.py", dir_dest)
        print(f"Copied tmux_conf files to user {dir_dest}")
        sys.exit(0)
    else:
        print(f"Skipping {p}")


print(f"ERROR: could not find a user {SP}!")
