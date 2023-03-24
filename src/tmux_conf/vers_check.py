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
    def __init__(self, actual_vers, requested_vers=None):
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
        v_min = parts[1]
        try:
            self.v_maj = int(v_maj)
        except ValueError as exc:
            print(f"Error: v_maj was not int: {self._vers}")
            raise ValueError from exc
        self.v_min, self.v_suffix = self.get_sub_vers(v_min)

    def get(self):
        """The version used for generating the config"""
        return self._vers

    def get_actual(self):
        """The version of the tmux bin"""
        return self._vers_actual

    def is_ok(self, vers) -> bool:
        """Checks version vs current tmux environment
        Param is forgiving, can be int, float or string.
        When given as int .0 is appended
        In many cases a float is sufficient, like 2.8, 3.0 etc
        Some versions have character suffixes like 3.3a, then a string
        param is needed. Internally version refs are allways treated as
        strings.
        """
        a, b = self.normalize_vers(vers).split(".")

        try:
            vers_maj = int(a)
        except ValueError as exc:
            print(f"ERROR: vers_ok({vers}) - maj part not int!")
            raise ValueError from exc

        vers_min, suffix = self.get_sub_vers(b)

        if vers_maj > self.v_maj:
            return False
        if vers_maj < self.v_maj:
            return True

        r = True
        if vers_min > self.v_min:
            r = False
        elif vers_min == self.v_min and suffix > self.v_suffix:
            r = False
        return r

    def get_sub_vers(self, v2: str):
        int_part = ""
        for c in v2:
            try:
                int(c)
            except ValueError:
                break
            int_part += c
        if not int_part:
            raise ValueError("sub_vers had no int part")
        i = int(int_part)
        s = v2.split(int_part)[1]
        return i, s

    def normalize_vers(self, vers) -> str:
        """Normalizes vers into a string"""
        # param fixes
        if isinstance(vers, str) and vers.find(".") < 0:
            try:
                vers = int(vers)
            except ValueError as err:
                print(f"ERROR: vers_check normalize_vers({vers}) bad param")
                raise ValueError from err
        if isinstance(vers, int):
            vers = f"{vers}.0"
        elif isinstance(vers, float):
            vers = f"{vers}"
        #  correct , -> .
        vers = vers.replace(",", ".")
        #
        #  Only keep first two items
        #
        parts = vers.split(".")
        # if len(parts) > 2:
        #     raise ValueError(f"ERROR: normalize_vers({vers}) > 2 parts")
        if len(parts) < 2:
            raise ValueError(f"ERROR: normalize_vers({vers}) < 2 parts")
        return ".".join(parts[:2])
