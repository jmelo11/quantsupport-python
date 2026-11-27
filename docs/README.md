# Build the Python documentation

With stable Rust and Python installed, run from this repository root. These are
the same guide and reference checks used by the Documentation workflow:

```sh
python -m pip install -r docs/requirements.txt "maturin>=1.5,<2.0"
maturin build --locked --release --out docs/_build/wheels
python -m pip install docs/_build/wheels/*.whl
python -m unittest discover -s tools/tests -p test_reference.py -v
python -m sphinx -W -b html docs docs/_build/html
```

The site is published at https://jmelo11.github.io/quantsupport-python/ by this
repository's Documentation workflow. API declarations are read from local type
stubs; canonical notebooks are rendered with their saved outputs. Executable
guide checks use the wheel built from this checkout. A rendering-only preview
can run the Sphinx command without building or installing the extension.
Only this repository's interface is built. Documentation deployment follows a
successful local Release workflow and uses its exact source tag. Pull requests
and pushes validate documentation; manual runs can select a published tag and
optionally a newer documentation revision for corrections.
