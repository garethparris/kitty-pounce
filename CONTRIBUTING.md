# Contributing

## Setup

```sh
uv sync
```

This installs pytest, ruff and pyright into `.venv/`.

## Type-checking

kitty is not pip-installable (there's no `kitty` package on PyPI that's the
actual terminal, and kitty's bundled Python can't see site-packages), so
`pounce.py`'s `TYPE_CHECKING`-only imports (`kitty.boss`, `kitty.tabs`,
`kitty.window`, `kitty.window_list`) can only be resolved for type-checking by
pointing pyright at a real kitty source checkout, cloned as a **sibling** of
this repo. Pin it to the version the README claims is verified (currently
v0.48.2), matching what CI's required `typecheck` job clones -- CI also runs
a second, non-blocking job against kitty's default branch to catch real API
drift early:

```sh
git clone --depth 1 --branch v0.48.2 https://github.com/kovidgoyal/kitty.git ../kitty
```

Then:

```sh
uv run pyright pounce.py   # strict -- this is the shipped file
uv run pyright tests       # basic -- pytest's dynamic fixtures don't suit strict mode
```

`pounce.py` doesn't actually depend on kitty's concrete `Boss`/`Tab`/`Window`
classes: it defines its own `BossLike`/`TabLike`/`WindowLike`/`WindowListLike`/
`WindowGroupLike` Protocols describing only the handful of members it
touches, each cited against the kitty source line it was verified from. A
`TYPE_CHECKING`-only function at the top of the file asserts that the real
classes still satisfy those Protocols, so a kitty upgrade that removes or
reshapes something `pounce.py` depends on fails the type check here rather
than failing silently at runtime.

## Running the tests

```sh
uv run pytest
```

The test suite never imports real kitty. `tests/fakes.py` provides
`FakeBoss`/`FakeTab`/`FakeTabManager`/`FakeWindowList`/`FakeWindowGroup`/
`FakeWindow` doubles that satisfy the same Protocols structurally, with no
kitty installation required.

## Linting and formatting

```sh
uv run ruff check .
uv run ruff format .
```

## Manual, in-kitty verification

Unit tests cover the pure logic; they can't prove kitty actually raises the
right OS window on a real keypress. Before relying on a change:

1. Point `kitty.conf` at your working copy of `pounce.py` (see
   `kitty.conf.example`).
2. Open 2+ OS windows with 2-3 tabs each, and at least one tab with a split
   (window) inside it.
3. Confirm one keypress = one jump, cycling through a tab's windows before
   moving to the next tab, with wraparound working in both directions, and
   that the target OS window is actually raised.

Because kitty re-reads, re-compiles and re-execs the kitten file on every
keypress (no module cache), edits take effect immediately -- no kitty restart
needed, just reload the config if you changed `kitty.conf` itself
(`ctrl+shift+f5`).
