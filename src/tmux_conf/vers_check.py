#  -*- mode: python; mode: fold -*-
#
#  Copyright (c) 2022: Jacob.Lundqvist@gmail.com
#  License: MIT
#
#  Part of https://github.com/jaclu/tmux-conf
#
#  See constants.py for version info
#
#  Class that handles version checking
#
#  See the README.md in the repository for more info
#


class VersionCheck:
    def __init__(self, actual_vers, requested_vers = None):
        self._vers_actual = self.normalize_vers(actual_vers)
        if requested_vers:
            self._vers = self.normalize_vers(requested_vers)
        else:
            self._vers = self._vers_actual
        #
        #  For performance, the version parts are pre-calculated
        #

        #
        #  tmux derivative tmate uses versions like 2.4.0
        #  for compatibility checks only the first two are needed
        #  This syntax handles both normal tmux and tmate
        #
        parts = self._vers.split(".")
        v_maj = parts[0]
        try:
            v_min = parts[1]
        except ValueError as exc:
            print(f"ERROR: Failed to parse version {self._vers}")
            raise ValueError from exc
        self.v_maj = int(v_maj)
        self.v_min, self.v_suffix = self.get_sub_vers(v_min)

    def get(self):
        """The version used for generating the config"""
        return self._vers

    def get_actual(self):
        """The version of the tmux bin"""
        return self._vers_actual

    def is_ok(self, vers) -> bool:
        """Checks version vs current tmux environment
        """
        v = self.normalize_vers(vers)
        try:
            a, b = v.split(".")
        except ValueError as exc:
            print(f"ERROR: vers_ok({v}) - bad syntax, expected maj.min notation!")
            raise ValueError from exc

        try:
            vers_maj = int(a)
        except ValueError as exc:
            print(f"ERROR: vers_ok({v}) - maj part not int!")
            raise ValueError from exc

        vers_min, suffix = self.get_sub_vers(b)

        if vers_maj > self.v_maj:
            return False
        if vers_maj < self.v_maj:
            return True

        r = True
        if vers_min > self.v_min:
            r = False
        elif suffix > self.v_suffix:
            r = False
        return r

    def get_sub_vers(self, v2: str) -> tuple[int, str]:
        int_part = ""
        for c in v2:
            try:
                int(c)
            except ValueError:
                break
            int_part += c
        i = int(int_part)
        s = v2.split(int_part)[1]
        return i, s

    def normalize_vers(self, vers) -> str:
        """Normalizes vers into a string"""
        # param fixes
        if isinstance(vers, int):
            vers = f"{vers}.0"
        elif isinstance(vers, float):
            vers = f"{vers}"
        #  correct , -> .
        vers = vers.replace(",", ".")
        return vers

