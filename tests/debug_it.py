#!/usr/bin/env python3
"""Sample config, showing how to use settings depending on a recent
tmux version. And defining some plugins of various complexity

Also shows various methods to define plugins
"""
from tmux_conf.tmux_conf import TmuxConfig

from .utils_test import CONF_FILE

# from local_tmux_conf.tests.utils import CONF_FILE


class WithContent(TmuxConfig):
    def content(self):
        self.write("bind -N")


#  First clear all plugins installed
WithContent(
    parse_cmd_line=False, conf_file=CONF_FILE, replace_config=True, tmux_version="3.0"
).run()
