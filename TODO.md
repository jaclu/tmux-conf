# TODO

## check if bin is tmux (or tmate)

```shell
#
#  Returns true and sets tmux bin & vers if this seems to be usable
#  otherwise returns False
#
assign_tmux_bin(tmux_bin="tmux"):
    parts = run_shell(f"{tmux_bin} -V").split(" ")
    if len(parts) != 2 or parts[0] not in ("tmux", "tmate"):
        if verbose:
            print("{tmux} Doesnt seem to be a tmux binary")
        return False
    try:
        maj,min = extract_tmux_vers(parts[1])
    except NOT_TMUX_VERS:
        if verbose:
            print("{parts[[1]} Doesnt seem to be a valid tmux version")
        return False
    self.tmux_bin = tmux_bin
    self.vers_maj = maj
    self.vers_min = min
    return True

extract_tmux_vers(vers_str_in):
    parts = vers_str_in.split(".")
    if len(parts) != 2:
        raise NOT_TMUX_VERS("Version string is not two parts separated by '.'")
    try:
        maj = int(parts[0])
    except VALUE_ERROR:
        raise NOT_TMUX_VERS(f"First part of version string is not int: {parts[0]}")

    #  loop over parts[1] as long as each char is an int, then
    #  ensure next char is a-z
    return maj, min
```
