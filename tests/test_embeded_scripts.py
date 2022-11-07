from tmux_conf.embedded_scripts import EmbeddedScripts

SCRIPT_NAME = "foo123"
CONF_FILE = "~/.tmux.conf"


def es_env(conf_file=CONF_FILE, use_embedded_scripts=True):
    return EmbeddedScripts(
        conf_file=conf_file, use_embedded_scripts=use_embedded_scripts
    )


def es_hello_world(use_embedded_scripts=True, use_bash=False):
    es = es_env(use_embedded_scripts=use_embedded_scripts)
    sh = [
        f"""
{SCRIPT_NAME}() {{
    echo "Hello world"
}}
    """
    ]
    es.create(SCRIPT_NAME, sh, use_bash=use_bash)
    return es


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


def test_es_content():
    es = es_hello_world()
    cont = es.content()
    errors = []
    if cont[1] != f"# {SCRIPT_NAME}() {{":
        errors.append(f"Bad script name line: {cont[1]}")
    if cont[2] != '#     echo "Hello world"':
        errors.append(f"Bad echo: {cont[2]}")
    assert not errors, "errors occured:\n{}".format("\n".join(errors))


def test_es_get_dir_embedded():
    test_pass = False
    es = es_hello_world()
    try:
        es.get_dir()
    except SyntaxError:
        test_pass = True
    assert test_pass is True  # noqa


def test_es_get_dir_external():
    es = es_hello_world(use_embedded_scripts=False)
    d = es.get_dir()
    assert d.endswith("/scripts")
