#
#  Copyright (c) 2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/my_tmux_conf
#

"""Embedded scripts package for tmux-conf.

This package provides functionality for managing and executing embedded
shell scripts within tmux configurations.
"""

from .scripts import EmbeddedScripts

__all__ = ["EmbeddedScripts"]
