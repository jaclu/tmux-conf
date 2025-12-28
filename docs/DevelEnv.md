# Devel Env

Install a reference to the live source using

## PyPi deploy

Create venv if need be: `python3 -m venv .venv`

Then prep and deploy to pypi

```shell
mkdir -p dist
rm -f dist/*
pip3 install -e .
pip3 install build twine
python3 -m build
python3 -m twine upload dist/*
```
