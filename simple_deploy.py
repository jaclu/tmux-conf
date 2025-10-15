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
#  Mostly for iSH, when installing a pip or building it locally
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

"""Simple deploy

This is mostly for iSH and other super slow nodes where just doing
pip install tmux-conf would take 5-10 minutes.
this directly copies the relevant files into the used site-packages.
"""

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

        d_src = "src/tmux_conf"
        d_dest = f"{p}/tmux_conf"
        # os.remove(f'{d_dest}*dist-info')
        if not os.path.isdir(d_dest):
            print(f"ERROR: dir {d_dest} does not exist!")
            sys.exit(1)
        shutil.copy(f"{d_src}/__init__.py", d_dest)
        shutil.copy(f"{d_src}/constants.py", d_dest)
        shutil.copy(f"{d_src}/embedded_scripts.py", d_dest)
        shutil.copy(f"{d_src}/plugins.py", d_dest)
        shutil.copy(f"{d_src}/tmux_conf.py", d_dest)
        shutil.copy(f"{d_src}/utils.py", d_dest)
        shutil.copy(f"{d_src}/vers_check.py", d_dest)
        shutil.copy(f"{d_src}/exceptions.py", d_dest)
        print(f"Copied tmux_conf files to user {d_dest}")
        sys.exit(0)
    else:
        print(f"Skipping {p}")


print(f"ERROR: could not find a user {SP}!")
