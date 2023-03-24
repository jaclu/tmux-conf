import os

import pytest
from src.tmux_conf.embedded_scripts import EmbeddedScripts

from .utils import CONF_FILE

SCRIPT_NAME = "foo123"


def es_env(conf_file=CONF_FILE, use_embedded_scripts=True):
    return EmbeddedScripts(
        conf_file=conf_file, use_embedded_scripts=use_embedded_scripts
    )


def es_hello_world(conf_file=CONF_FILE, use_embedded_scripts=True, use_bash=False):
    es = es_env(conf_file=conf_file, use_embedded_scripts=use_embedded_scripts)
    sh = [
        f"""
{SCRIPT_NAME}() {{

    echo "Hello world"

}}

"""
    ]
    sh.append("")
    es.create(SCRIPT_NAME, sh, use_bash=use_bash)
    return es


def get_shebang(fname):
    with open(fname, encoding="utf-8") as f:
        line = f.readline()  # Just get 1st line
    return line.strip()


def test_es_relative_conf_file():
    conf_file = "dummy_conf"
    es = es_env(conf_file)
    print(f">> conf_file: {es._conf_file}")
    assert es._conf_file.split("/")[-1] == conf_file


def test_es_XDG():
    os.environ["XDG_CONFIG_HOME"] = "/tmp"
    es = es_hello_world(use_embedded_scripts=False, use_bash=True)
    bash_sh = es.run_it(SCRIPT_NAME).split('"')[1]
    os.environ.pop("XDG_CONFIG_HOME")
    # Simplify by not caring about path to bash
    assert get_shebang(bash_sh) == "#!/usr/bin/env bash"


def test_es_create_external_bash():
    es = es_hello_world(use_embedded_scripts=False, use_bash=True)
    bash_sh = es.run_it(SCRIPT_NAME).split('"')[1]
    # Simplify by not caring about path to bash
    assert get_shebang(bash_sh) == "#!/usr/bin/env bash"


def test_es_create_external_sh():
    es = es_hello_world(use_embedded_scripts=False)
    bash_sh = es.run_it(SCRIPT_NAME).split('"')[1]
    # Simplify by not caring about path to bash
    assert get_shebang(bash_sh) == "#!/bin/sh"


def test_es_run_it_posix():
    es = es_hello_world()
    assert es.run_it(SCRIPT_NAME) == f'run "cut -c3- {CONF_FILE} | sh -s {SCRIPT_NAME}"'


def test_es_run_it_bash():
    es = es_hello_world(use_bash=True)
    s = es.run_it(SCRIPT_NAME)
    # Simplify by not caring about path to bash
    assert (
        s.startswith(f'run "cut -c3- {CONF_FILE} | ') is True
        and s.endswith(f'/bash -s {SCRIPT_NAME}"') is True
    )


def test_es_run_it_in_bg():
    es = es_hello_world()
    assert (
        es.run_it(SCRIPT_NAME, in_bg=True)
        == f'run -b "cut -c3- {CONF_FILE} | sh -s {SCRIPT_NAME}"'
    )


def test_es_content():
    es = es_hello_world()
    cont = es.content()
    errors = []
    if cont[1] != f"# {SCRIPT_NAME}() {{":
        errors.append(f"Bad script name line: {cont[1]}")
    if cont[3] != '#     echo "Hello world"':
        errors.append(f"Bad echo: {cont[2]}")
    assert not errors, "errors occured:\n{}".format("\n".join(errors))


def test_es_get_dir_embedded():
    es = es_hello_world()
    with pytest.raises(SyntaxError):
        es.get_dir()


def test_es_get_dir_external():
    es = es_hello_world(use_embedded_scripts=False)
    d = es.get_dir()
    assert d.endswith("/scripts")


def test_es_get_dir_external_def_conf():
    es = es_env(conf_file="~/.tmux.conf", use_embedded_scripts=False)
    d = es.get_dir()
    assert d == f"{os.getenv('HOME')}/.tmux/scripts"


def test_es_get_dir_external_rel_conf():
    es = es_env(conf_file="tmux.conf", use_embedded_scripts=False)
    d = es.get_dir()
    assert d.endswith("/tmux/scripts")
