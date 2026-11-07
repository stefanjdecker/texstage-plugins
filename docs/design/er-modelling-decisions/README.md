# ER Modelling Decisions: worked design examples

These fictional examples accompany the [design](../er-modelling-decisions.md),
[draft contract](../er-modelling-decisions-contract.md) and
[implementation plan](../er-modelling-decisions-plan.md).
They are specification aids, not installable activities or final author schemas.

| Fixture | Decisions | Hand-derived expectation |
| --- | --- | --- |
| `registrations.json` | 3 participation choices × 3 attribute owners × 3 relationship forms | 27 combinations; exactly 2 pass the finite checks |
| `rooms.json` | 4 identification choices | Owner identification and surrogate + scoped uniqueness pass; global number and surrogate alone fail |
| `mentoring.json` | 2 mentor minima × 3 interpretation states | 2 conditional passes, 2 contradictions, 2 unresolved discussion cases |

The registration alternatives are a binary relationship carrying status and a
reified entity carrying status with unique (person, workshop). The room
alternatives are owner + number and surrogate + unique (building, number).
Passing these examples does not prove general equivalence.

Some observations are deliberately **forbidden business situations**, not bad
JSON: two occurrences for the same registration pair, for example. Record IDs
identify observations; they do not implicitly satisfy the business key.

`expected-cases.json` records the permitted answer combinations and named
counterexamples independently of the checker. The mentor case explicitly
leaves one requirement open. Selecting an assumption changes only the expected
admission of an unused mentor, not the fact that each student has one mentor.

From the collection root:

```sh
python maintenance/check_er_design.py
```

The default is read-only and compares fixtures against the committed
`validation.json`. To intentionally refresh that record after reviewing a
changed design:

```sh
python maintenance/check_er_design.py --write-report
```

The standard-library checker enumerates all 37 combinations, checks the
hand-derived outcomes and specific witnesses, and records source/checker
SHA-256 hashes. It evaluates uniqueness, functional dependencies and degree
with zero-link entities. It is intentionally a small trusted-input model of
these three scenarios, not the proposed general compiler, an untrusted-input
validator, an installed browser engine or a proof of unbounded equivalence.

Runtime parsing, host portable-schema conformance, privacy, concurrency,
serialized budgets, rendering and classroom performance remain untested here.
The examples use English data labels; production English/German UI and
non-ASCII boundary coverage are later gates.
