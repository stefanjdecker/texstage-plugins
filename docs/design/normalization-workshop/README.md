# Normalization Workshop: reviewable examples

The original design fixtures are now shipped and checked by the
[analyzer](../../../plugins/normalization-workshop/README.md). N3 now supplies a
[working LaTeX workshop](../../../examples/normalization/lesson.tex) and
[user guide](../../normalization-workshop.md). See the [design](../normalization-workshop.md),
[draft contract](../normalization-workshop-contract.md) and
[implementation milestones](../normalization-workshop-plan.md).

## Contents

- [Registration lesson source](registration.lesson.draft.json): a BCNF task
  requiring losslessness and dependency preservation, with one worked answer.
- [Tutor lesson source](tutor.lesson.draft.json): a lossless BCNF task that
  exposes the loss of dependency preservation.
- [Expected cases](expected-cases.json): 17 hand-specified finite expectations.
- [Validation record](validation.json): reproducible checker results and input
  hashes, not installed-package or performance evidence.

The historical `.draft.json` filenames are retained for continuity; their
envelopes validate against the frozen lesson schema and compile with
`model.check_lesson`. This is not yet a TeX authoring hook. They must not be passed to an existing relational plugin.
Wire masks are for compact serialization only. The planned UI and PDF show
attribute names. For registration, bits follow S,N,C,T,I,O: SN=3, SC=5,
CTI=28, IO=48. For the tutor exercise, S,T,U gives SU=5 and TU=6.

## What a learner should see

The registration business rules are S -> N, C -> T,I and I -> O.
Start with two synthetic tuples:

| S | N | C | T | I | O |
| --- | --- | --- | --- | --- | --- |
| s1 | Ada | c1 | Databases | i1 | Room 1 |
| s2 | Bo | c2 | Networks | i2 | Room 2 |

The dependencies hold. The original records say Ada takes Databases and Bo
takes Networks. If we retain only SN, CTI and IO, their join also associates
Ada with Networks and Bo with Databases. Each table is BCNF and the dependencies
remain enforceable locally, but the decomposition is lossy. The SC table
preserves the associations. This example demonstrates why checking “all
attributes still appear” is insufficient.

For the tutor exercise, ST -> U and U -> T. The original is 3NF: its keys
are ST and SU, so all attributes are prime. U -> T violates BCNF because
U does not determine S. Decompose into SU and TU. Both are BCNF and the join
is lossless, but ST -> U is no longer enforceable using only local FDs.

A concrete local state explains the lost constraint:

| SU: Student | Tutor |
| --- | --- |
| s1 | u1 |
| s1 | u2 |

| TU: Tutor | Topic |
| --- | --- |
| u1 | t1 |
| u2 | t1 |

Both components satisfy their projected FDs. Their join gives student s1 two
tutors for topic t1, violating ST -> U. This is a dependency-preservation
counterexample, distinct from a spurious-tuple counterexample to losslessness.
Losslessness concerns projections of a *legal original relation*; it does not
say arbitrary locally legal component states satisfy every original constraint.

## Intended authoring after implementation

The standalone example deck will have closure/key discussion slides followed
by classification and decomposition items. An optional combined deck can use
[FD Lab](../functional-dependencies.md) for interactive foundation tasks. A
future normalization sidecar entry would be:

```json
{
  "format": 1,
  "language": "en",
  "items": [
    {
      "id": "registration",
      "type": "io.github.stefanjdecker.normalizationworkshop.workshop",
      "source": "activities/registration.json"
    }
  ]
}
```

After installing, explicitly enabling and pinning the future provider, the
proposed style would place the item:

```tex
\usepackage{texstage}
\usepackage{texstage-normalization-workshop}
% Inside a beamer frame:
\normalizationworkshop{registration}{.96\linewidth}{.72\textheight}
```

These snippets document the planned interface; they are not working installation
instructions. Sources resolve relative to the master deck directory under the
existing host confinement rules. The future guide must include actual artifact
versions/payload pins and build commands when those artifacts exist.

## Reproduce the design checks

From the collection root, using Python 3.12+ and no extra dependencies:

```sh
python maintenance/check_normalization_design.py
```

The default command is read-only. To deliberately refresh the evidence after a
reviewed change:

```sh
python maintenance/check_normalization_design.py --write-record
```

The checker verifies all 17 cases, both draft worked answers, and 49,152 binary
losslessness comparisons: all 4,096 subsets of the 12 nontrivial singleton FDs
over three attributes, each with the 12 distinct covered binary decompositions.
This includes empty determinants. It compares the tableau chase with the
independent binary closure criterion. Losing tableaux are checked to satisfy
the FDs while their missing distinguished tuple belongs to the join.

Fixture checks also compare preservation using explicitly projected FDs against
iterated projected closures. The cases cover missing coverage, implied projected
dependencies, preservation by a chain, multiple/empty keys, constants, no FDs,
cycles, contained components and multiway lossless/lossy decompositions.

The expected values are specified separately from the checker. This does not
test the future JavaScript/Python implementations, hostile JSON validation,
schemas, byte/time budgets, UI, accessibility, privacy, installed wheels,
browsers, physical phones, classroom load or hosted CI. Those remain N1–N6.
