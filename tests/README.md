# Testing

Test requirements are specified as an extras-require.
Run from the root of this repo:

```shell
pip install -e . -r tests/requirements.txt
```

Then invoke tests using:

```shell
pytest
```

There is a packaging test which is intentionally kept separate because it's
a) very slow and b) unlikely to change.
To avoid running it use:

```shell
pytest tests
```
