#
#  Copyright (c) 2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/my_tmux_conf
#

"""
registry
"""

from typing import Any

from .spec import ScriptSpec


class ScriptRegistry:  # pylint: disable=too-few-public-methods
    """
    Docstring for ScriptRegistry
    """

    def __init__(self) -> None:
        self._defined: set[Any] = set()  # user-defined scripts
        self._built_in_accepted: set[Any] = set()

    def accept(self, spec: ScriptSpec) -> bool:
        """User-defined scripts always register"""
        if not spec.built_in:
            self._defined.add(spec.name)
            return True

        # Built-in scripts only register if not overridden
        if spec.name in self._defined:
            return False

        if spec.name not in self._built_in_accepted:
            self._built_in_accepted.add(spec.name)
            return True

        return False
