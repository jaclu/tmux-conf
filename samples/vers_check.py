#!/usr/bin/env python3
#
#  Copyright (c) 2022: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  This will generate a mostly empty config file that is not really
#  usable for tmux, sole purpose is to explore version checks.
#

# pylint: disable=import-error
from tmux_conf import TmuxConfig


# pylint: disable=too-few-public-methods
class DummyConfig(TmuxConfig):
    def content(self):
        w = self.write  # shortcut for writes

        w("# vvvvv   Version checked item below this   vvvvv")
        w()  # spacer

        #
        #  Try changing this to above your current version,
        #  to see how version checks work!
        #
        #  Run it with something like: ./vers_check.py ~/foo.conf -r
        #  then do:  less ~/foo.conf
        #  And check for what was written to the config file
        #
        min_version = "2.4"

        if self.vers_ok(min_version):
            w("# Accepable version")
        else:
            w("# tmux to old")

        w()  # spacer
        w("# ^^^^^   version check is above            ^^^^^")


if __name__ == "__main__":
    DummyConfig().run()
