# Build the Python documentation

You need stable Rust and Python. Run these commands from the repository root.
They are the same guide and reference checks that the Documentation workflow
runs:

```sh
python -m pip install -r docs/requirements.txt "maturin>=1.5,<2.0"
maturin build --locked --release --out docs/_build/wheels
python -m pip install docs/_build/wheels/*.whl
python -m unittest discover -s tools/tests -p test_reference.py -v
python -m sphinx -W -b html docs docs/_build/html
```

To preview the pages only, run the last command on its own. You do not need to
build or install the package for that.

## How the site is built

- The API reference is generated from the package's type stubs (`.pyi` files).
- Example notebooks are shown with their saved outputs; they are not run during
  the build.
- The guide examples are run against the wheel built from this checkout.
- The site covers only the Python package.

## Publishing

This repository's Documentation workflow publishes the site at
https://jmelo11.github.io/quantsupport-python/.

- Pull requests and pushes build and check the documentation.
- After a successful Release workflow, the site is deployed from that
  release's source tag.
- To correct published pages, run the workflow manually. Select a published
  tag and, optionally, a newer documentation revision.
