# Functional dependencies for TeXStage

`fd-closure` asks students for the closure of a starting set of attributes.
TeXStage groups equivalent answers and awards any points configured in the deck.
The package supplies the activity through the `texstage.kinds` entry point.

## Install and run the example

Install TeXStage 1.0.1.dev2 or later using its source installation and locked
dependencies. On both the build machine and the presenting server, run the
following commands from this package directory in the TeXStage environment.

```console
python -m pip install --no-build-isolation .
texstage kinds check fd-closure
```

Restart a running server after installing the kind. To present the two-slide
example from this checkout, run the following on the presenting machine.

```console
texstage present src/texstage_kinds_fd/examples/closure.tex
```

The same example ships in the wheel under `texstage_kinds_fd/examples/closure.tex`.

To run the classroom regression against installed wheels, install the host's
locked development dependencies and run `python -m pytest tests/test_classroom.py`
from this directory. It uses TeX and Chrome, a temporary server and two mobile
browser sessions to check feedback and scoring through the presenter reveal.

## Write a question

Put the problem statement in `\prompt` so students see the relation,
dependencies and starting set on the slide and their phones. Configure the
checker with the same facts.

| Activity option | Meaning | Example |
| --- | --- | --- |
| `attributes` | Distinct, case-sensitive attribute names in schema order | `attributes={A,B,C,D}` |
| `dependencies` | Comma-separated rules with space-separated attributes on each side. An empty left side expresses a constant | `dependencies={B C -> D,A -> B C}` |
| `start` | Starting attributes. An omitted or empty list starts at the empty set | `start={A}` |

Use up to 40 attributes and 40 dependencies. Each attribute name starts with an
ASCII letter, uses up to 60 ASCII letters, digits or underscores, and is
case-sensitive. The complete comma-separated schema must fit the 100-character
phone input. Students may enter names in any order, with commas, spaces or
braces. Repeating an attribute leaves the set unchanged. Both `{}` and `∅`
denote the empty set.

The build computes the closure and writes it to the bundle's private keys. An
optional `\reference{...}` cross-checks an instructor's worked answer at build
time. The standard `feedback=status` setting shows whether an entry parsed.
The reveal shows correctness, and `points=standard` awards points for a correct
answer. See the [example deck](src/texstage_kinds_fd/examples/closure.tex).
