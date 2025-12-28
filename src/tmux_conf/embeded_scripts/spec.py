#
#  Copyright (c) 2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/my_tmux_conf
#

"""
Dataclass defining a script
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScriptSpec:
    """
    Docstring for ScriptSpec
    """

    name: str
    lines: list[str]
    use_bash: bool
    built_in: bool
