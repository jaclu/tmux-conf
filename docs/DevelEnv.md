# Devel Env

Install a reference to the live source using

## PyPi deploy

```shell
mkdir -p dist || exit 1
rm -f dist/*
pip3 install -e . || exit 1
pip3 install build twine || exit 1
python3 -m build || exit 1
python3 -m twine upload dist/*
```
