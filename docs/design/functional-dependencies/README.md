# FD Lab: worked design examples

These named sources and mathematical cases are accepted by the implemented
[F1 engine/model](../../../plugins/fd-lab/README.md). They are not yet a runnable
classroom deck: prepared authoring, style and phone interfaces remain pending. See the
[design](../functional-dependencies.md), [draft contract](../functional-dependencies-contract.md)
and [implementation plan](../functional-dependencies-plan.md).

## Workshop sequence

Attribute order is `person,email,workshop,tutor,room,building` (P,E,W,T,R,B).
The assumed FDs are `P → E`, `E → P`, `W → TR` and `R → B`. A workshop has
one tutor and room; a room belongs to one building; person and registered email
identify each other. These are explicit teaching assumptions, not deductions
from a sample table. Tutors and buildings can be shared by different workshops.

| Example ID | Task | Worked result |
| --- | --- | --- |
| `workshop_closure` | Compute W's closure with steps | `{W,T,R,B}`, using f3 then f4 |
| `workshop_one` | Find one candidate key | `{P,W}`; `{E,W}` is equally valid |
| `workshop_all` | Find every candidate key | `{P,W}` and `{E,W}` |
| `workshop_implied` | Does W determine B? | Yes, derive TR then B |
| `workshop_refuted` | Does T determine W? | No; two tuples may agree only on T |
| `different_sizes` | All keys under A → BC, BC → A | `{A}` and `{B,C}`; minimal does not mean smallest |
| `no_fds` | All keys on ABC with no given FDs | `{A,B,C}` |
| `empty_key` | All keys under ∅ → A, A → B | The empty key, represented by a list containing an empty set |
| `cycle_and_free` | All keys under A → B, B → A, A → A | `{A,C}` and `{B,C}` |

For the negative workshop implication, use two symbolic rows:

| Row | P | E | W | T | R | B |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1 | 1 | 1 | 0 | 1 | 1 |

Every premise FD holds: the rows differ on each premise determinant. They
agree on T but differ on W, refuting T → W. A second valid answer also agrees
on B. The plugin must accept both, rather than compare them to a single reference.

## Files and reproduction

| File | Role |
| --- | --- |
| [lesson-v1.schema.json](lesson-v1.schema.json) | Draft named authoring envelope, including worked answer and feedback policy |
| [answer-v1.schema.json](answer-v1.schema.json) | Draft compact wire variants; semantic checks additionally enforce the actual task and masks |
| [examples.json](examples.json) | Nine synthetic lessons and hand-derived expected mathematical results |
| [expected-cases.json](expected-cases.json) | 21 correct and incorrect wire answers with expected acceptance and feedback category |
| [validation.json](validation.json) | Reproducible checker result, input hashes and explicit exclusions |

The `examples` wrapper and its `expected` sections are a design-test format.
An eventual authoring file contains just one entry's `lesson` object. Named
worked answers compile to compact masks/indices internally. Students and
teachers see attribute names; they do not need to learn the wire encoding.
The public repository contains these synthetic solutions deliberately; real
preparation will keep worked answers out of initial public transport.

From the collection root, using the compatible host's locked development
environment (which supplies `jsonschema`):

```sh
python maintenance/check_fd_design.py
```

Normal execution checks and prints a report without changing files. Use
`--write-report` only to refresh the tracked validation record after intentional
fixture/checker edits. It records input hashes, not a claim of a released artifact.

The checker compares forward closure with intersection of all closed attribute
sets; it compares single-removal key tests with exhaustive proper-subset tests.
It checks all 4,096 theories formed from the 12 nontrivial singleton-right FDs
over three attributes, including empty determinants: 32,768 closure comparisons.
It also verifies constructed counterexamples by actual two-row cell comparisons,
the nine named examples, all 21 submitted-answer cases, eight invalid cases,
alternative proof orders, target-prefix proofs and an eight-attribute case with
16 candidate keys. This finite evidence does not replace the reviewed general
semantics or independently implemented production Python/JavaScript engines.

The conservative structural transport example uses 949 bytes for an answer,
4,608 bytes for typed data and 4,801 bytes for a transported outcome, with ASCII
escaping. It deliberately overestimates candidate-key output by listing all
256 subsets; these cannot all be minimal keys. It is a serialization bound,
not a valid mathematical analysis or a result-schema/host-validation test.
Result/view schemas, installed artifacts, TeX output, browser security, state
races, physical phones and classroom throughput remain implementation gates.
