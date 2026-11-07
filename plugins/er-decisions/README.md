# ER registration modelling, authoring and lesson state

This experimental engine checks modelling decisions against a fixed collection
of permitted and forbidden situations. It returns constraint witnesses, not
a grade based on copying one diagram. The registration example accepts both a
relationship with status and an association entity with pair uniqueness.

Version 0.6.0 retains prepared LaTeX exercises and solutions in English and German,
including both checked models and selected counterexamples. See the
[authoring guide](../../docs/er-decisions-authoring.md) for installation,
enablement, the `\erdecisions` command and all output editions.
The live lesson now includes English/German phone decision cards, a public-only
model preview, explicit submission and repair, and presenter inspection/sharing.
See the [classroom guide](../../docs/er-decisions-lesson.md) and the
[state contract](../../docs/er-decisions-state.md). Rooms, scoped identification
and unresolved assumptions remain later engine profiles.

The 0.4.1 accessibility update links errors to their fields, returns focus to
visible controls after draft conflicts, and announces phase/answer changes
without repeating unchanged messages. Keyboard and accessibility-tree checks
supplement the [remaining manual review](../../docs/er-decisions-accessibility.md).

## Build and try

Use a fresh Python 3.12+ environment with the matching installed TeXStage
host wheel and its locked development/build requirements. The required local
host implements manifest revision 4 and typed results; its development version
alone does not identify the tested artifact. See the validation record in
the collection's `docs/design/er-points-validation.md`. Version 0.6.0 requires
TeXStage 0.2.1.dev5 with bounded item records and actor-scoped updates. Its
state schema is 4; old sessions must continue in their original pinned environment.

The deterministic engine opts into the host's bounded result cache. Identical
inputs in the same exercise and round can reuse a previously validated successful
result. The registration exercise has 27 answer combinations. Different inputs
still execute in fresh restricted workers; each student retains an independent
durable job, answer version, receipt and private feedback. Reset starts a new
cache scope. Errors, stale results and results from other exercises are not reused.

From the collection root:

```console
npm ci --ignore-scripts
npm run build:workers
npm run check:workers
python maintenance/build_wheels.py --package er-decisions
python -m pip install --no-deps dist/texstage_er_decisions-0.6.0-py3-none-any.whl
python -m pytest plugins/er-decisions/tests -q
python maintenance/er_probe.py --output artifacts/er-decisions
```

The probe uses the installed wheel, Node and both host result validators.
Run `node maintenance/er_browser.cjs artifacts/er-decisions` for the actual
host evaluator under its production worker policy. Select Firefox or WebKit
with the `BROWSER` environment variable. Browser binaries must be installed.
Use a writable temporary directory via `ER_TEST_TMP` if the platform requires it.

The wheel consumes committed worker output; Node is a maintainer/test tool,
not required for end-user installation. Installation does not enable code.
Prepared authoring must explicitly enable/pin provider
`io.github.stefanjdecker.erdecisions` in a separate profile. Engine ID:
`io.github.stefanjdecker.erdecisions.model`. The prepared content type is
`io.github.stefanjdecker.erdecisions.lesson`. Deck uploads cannot install it.

## Frozen registration profile

`fixtures/registrations.json` is the complete seed. Four versioned schemas
cover exercise, model, answer and result. They are closed and use the host's
portable schema vocabulary. Additional semantic validation checks references,
ID uniqueness, disjoint slot ownership, observation types, all bounded option
combinations and each worked answer.

The profile contains exactly two entity types and one binary relationship,
up to four observed scalar attributes and four decisions. It supports
per-role bounds, attribute ownership and relationship reification. It uses
opaque occurrence identities for the endpoint entities; selectable entity
keys are outside this profile.

An answer contains only selected IDs:

```json
{"format":1,"choices":[
  ["person-links","zero-many"],
  ["status-owner","registration"],
  ["registration-form","entity-pair-key"]
]}
```

The evaluator returns all check IDs exactly once, with expected/actual admission
and a small witness for a failed model constraint. A witness can explain why a
model excludes an allowed situation or rejects a forbidden one; admission of a
forbidden situation has no violated-model-constraint witness because the model
failed to prohibit it.

Several correct choices retain distinct canonical identities. A finite pass
is not proof of general ER equivalence. The lesson now supports bounded rationale, classroom phases, checked feedback
and explicit release. Version 0.6.0 accepts up to 600 distinct responding students
per activity. Individual answers are stored separately; class totals and the
presenter's 16-answer pages stay bounded. Phones receive their own answer
updates, while class-wide counts remain on the presenter. The release checklist
records measured latency and the remaining physical-phone and deployment checks.

See the [frozen runtime contract](../../docs/design/er-registration-engine-contract.md)
for exact limits, normalization, evidence ordering and unsupported features.

## Optional activity points

Add `"points": 1000` at the top level of the lesson JSON. Omission or zero keeps
practice mode and its existing repair workflow. A verified fully correct model
earns the configured amount (0–10,000); either accepted modelling alternative
qualifies. Incorrect models earn zero. Pending, unavailable or unverified results
do not receive a correctness award. There is no speed or streak bonus.

Points reach the game total, rank and CSV only when the presenter reveals the
alternatives. Accepted pending work can finish after reveal and receive its award.
Replacing an answer before reveal replaces its credit; retries cannot add another
award. A scored round cannot reopen after reveal. Reset removes this activity's
points and starts a new round. Navigation preserves the award.

To build a disposable scored example from the existing single source:

```console
python maintenance/er_ui_bundle.py --output artifacts/er-scored --points 1000
```

Use `--language de` for German. Phone and presenter views explain the rule, and
the phone displays its released activity points. Existing source files with no
points field remain practice activities. Use a freshly pinned bundle and session.
