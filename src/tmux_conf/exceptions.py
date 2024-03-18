#  -*- mode: python; mode: fold -*-
#
#  Copyright (c) 2022-2024: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See the README.md in the repository for more info
#
"""tmux-conf exceptions"""


class TmuxConfNotTmuxCommand(Exception):
    """Command does not seem to be tmux"""

    def __init__(self, message="Invalid tmux command"):
        self.message = message
        super().__init__(self.message)


class TmuxConfInvalidTmuxVersion(Exception):
    """Version is not valid tmux version"""

    def __init__(self, message="Invalid tmux version string"):
        self.message = message
        super().__init__(self.message)
