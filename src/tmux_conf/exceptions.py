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
