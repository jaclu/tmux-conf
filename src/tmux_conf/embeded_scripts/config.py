#
#  Copyright (c) 2025: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/my_tmux_conf
#

"""a data class, defining how a script should be defined in tmux.conf"""

from dataclasses import dataclass

from ..vers_check import VersionCheck


@dataclass(frozen=True)
class RunCmdConfig:
    """
    Docstring for RunCmdConfig
    """

    conf_file: str
    use_embedded: bool
    plugin_handler: str
    vers: VersionCheck  # the VersionCheck instance
