# Devel Env

Install a reference to the live source using

`pip3 install -e .`

## PyPi deploy

```shell
python3 -m build
rm dist/*
python3 -m twine upload dist/*
```
