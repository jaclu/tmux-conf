#  -*- mode: python; mode: fold -*-
#
#  Copyright (c) 2022-2024: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#

"""base packet imports"""

from .constants import __version__
from .tmux_conf import TmuxConfig

__all__ = ["TmuxConfig", "__version__"]
