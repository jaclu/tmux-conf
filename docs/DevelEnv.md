# Devel Env

Install a reference to the live source using

## PyPi deploy

```shell
pip3 install -e .  # Install a reference to the live source
pip3 install build
mkdir -p dist
rm -f dist/*
python3 -m build
python3 -m twine upload dist/*
```
