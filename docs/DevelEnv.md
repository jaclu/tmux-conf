# Devel Env

Install a reference to the live source using

## PyPi deploy

Create venv if need be: `python3 -m venv .venv`

Then prep and deploy to pypi

```shell
mkdir -p dist || exit 1
rm -f dist/*
pip3 install -e . || exit 2
pip3 install build twine || exit 3
python3 -m build || exit 4
python3 -m twine upload dist/* || exit 5
```
