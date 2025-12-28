#
#  Copyright (c) 2022-2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#
#  See the README.md in the repository for more info
#

"""Plugin management package for tmux-conf.

This package provides comprehensive plugin management for tmux configurations,
including:
- Plugin registration and version checking, ignoring any plugin that depends
on a more recent tmux
- Plugin deployment (TPM or manual)
- Plugin display and reporting
"""

from .manager import Plugins

__all__ = ["Plugins"]
