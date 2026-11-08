# Combined database example validation

Validated locally on Windows on 2026-11-08, using installed portable wheels and
a fresh operator profile, in English and German. This is evidence for the combined example, not a new
plugin release or a physical-classroom acceptance claim.

## Source and artifacts

- Collection base: 1c5d922d35689c4460c3b62a6b970b9a5564eb12.
- Host base: e7351a5f10018d4c0c11e1d65059046248929ca7, plus the companion
  phone content-selection fix on codex/database-activity-examples.
- Ten provider wheels built from this collection, with source-distribution
  payload parity checked by maintenance/build_wheels.py. The coordinate wheel
  was rebuilt with its English/German resources and rechecked for parity.
- [validation.json](validation.json) records wheel hashes, host changes and
  the exact exercise-source hashes used for these checks.
- The host base alone does not contain the phone fix. The version string remains
  0.2.1.dev7; use the matching source and artifact identity, not just that string.

The bilingual example, coordinate translations and host fix are local,
uncommitted work at validation time.
No hosted CI or package publication is claimed for them.

## Build and content

The live bundle contains all eight installed content-type capabilities:
coordinates, ER decisions, relational algebra, query planning, B+ trees,
functional dependencies, normalization and transactions. The distance and
transaction engines are exercised through their dependent activities.

| Check | Result |
| --- | --- |
| Language editions | English (`en`) and German (`de`); counts below apply to each |
| Logical frames / files included by the master | 70 / 70 |
| Built-in quizzes | 10, covering all nine types |
| Built-in SQL/SPARQL/Turtle/shared-graph activities | 12 |
| Plugin examples | 31, including 30 prepared sources |
| Handout / solutions PDFs | 70 pages each |
| Stage / static PowerPoint slides | 90 each; quiz phases expand logical frames |
| Stage PDF | 180 pages including presenter-note pages |
| Build warnings, layout findings, handout overfull boxes | 0 |
| Characters outside either handout or solution page | 0 |
| Private keys exposed through the bundle public-file API | None |
| Prepared items missing from the live bundle | None |

All four handout/solution PDFs were rendered to PNG and visually reviewed, with
full-page checks of dense B+ and plan material. Prepared exercise/solution generation
validated each worked answer. The source confinement policy remains unchanged:
all copied exercise sources stay beneath the master directory.

The built-in reference checker passed ten reference exercises, five alternative
SQL queries, five plausible SQL mistakes, RDF alternatives/counterexamples,
two transfer-data probes and refused SQL mutations.

## Language selection and content parity

The masters use `english` and `ngerman` Babel respectively. Their activity
sidecars use `en` and `de` and have identical item/source bindings. The masters
share their slide order, layout, data and reference answers. German frame text,
quiz prompts, explanations, presenter notes and built-in static labels are
authored explicitly. Transaction titles/prompts identify the same six scenarios
in both languages. SQL/RDF identifiers and literal data values remain unchanged.
See the [language guide](../../docs/languages.md).

Coordinate labels, status text, decimal formatting and accessible grid names
now follow `ctx.language`. Its revision-1 distance engine still returns its
original English text summary; the renderer translates that known display
format. Structured evaluation status and the server's coordinate comparison
remain authoritative. An unrecognized successful summary gets neutral checked
feedback; errors never become success through text parsing.

The isolated coordinate/distance scenario passed all five pytest checks with
exactly those two installed providers. This includes the new installed-wheel
locale regression (regional German tags, English fallback, decimal formatting,
queued/timeout/error states and unfamiliar summaries). The run emitted a
Starlette deprecation warning and a Windows pytest-cache write warning; neither
affected test execution or its results.

## Browser rehearsal

Both final bundles and the installed host/provider wheels were exercised in
Chromium 151.0.7922.34, Firefox 153.0 and WebKit 26.5, with presenter, projector,
and 390-pixel phone contexts: six passing runs. Each used the opposite browser
locale (German deck/English browser, English deck/German browser) and passed:

- All ten built-in code references through the real presenter evaluator and
  participant save/reveal flow.
- Both shared-graph input forms, including approval/agreement gates.
- Mount, open-answer/prediction controls and teardown for all 31 plugin examples.
- Coordinate keyboard submission, touch submission, reset, translated distance
  feedback and accessible labels; correct-point reveal and rejection of a
  different point at the same distance.
- Deck-language projections for every plugin and role, localized presenter
  controls, and the expected phone submission label for every plugin example.
- A saved prediction of 110 in the transaction counter example.
- Navigation from retained built-in activity feedback into the plugin examples.
- No horizontal phone overflow and no JavaScript page errors.

These are combined-deck smoke checks. They do not repeat every grading,
sharing, retry, capacity or accessibility scenario already covered in the
focused provider suites. The ten built-in quizzes were built and checked for
complete type coverage; this rehearsal did not submit every quiz variant.

[browser-smoke.cjs](browser-smoke.cjs) reproduces the mixed-deck workflow; the
[README](README.md#edit-and-verify) gives its commands. Screenshots and temporary
profiles remain in ignored build output, outside the public source files.

## Host issue found by combining examples

Built-in activity feedback remains available after leaving its slide. The phone
previously selected that retained activity ahead of a current plugin's input.
The companion host change gives current plugin input priority, preserving the
existing precedence of an active quiz and a finished session.

Five targeted pytest checks passed, including the Node phone regression and
plugin lifecycle/evaluator/assets/keyboard suites. The regression covers the
mixed state, get-ready/open quiz precedence, revealed quizzes, finished sessions,
and plugins without a phone surface. Worker CSP, validation, execution deadlines
and persistence are unchanged.

## Phone-language follow-up

TeXStage commit `79d5f3d76b6dd9f6348e65672867d00e40a70ef0` adds session language
to the general phone interface, including the join form before login. Its
language-only PIN lookup shares the existing wrong-PIN throttle. The earlier
build and mixed-deck evidence above remains a record of its original artifacts.

The follow-up passed 43 targeted server, phone and plugin-language tests, plus
English and German browser runs in Chromium, Firefox and WebKit. Each browser
used the opposite locale and checked joining, waiting, resume, duplicate-name
errors, Q&A, a quiz, SQL input and draft preservation. Manual PIN entry and a
delayed response for an old PIN were also checked. All runs reported no page
errors. [phone-language-validation.json](phone-language-validation.json) records
the tested wheel and browser results. The host's
[browser regression](https://github.com/stefanjdecker/texstage/blob/79d5f3d76b6dd9f6348e65672867d00e40a70ef0/maintenance/phone_language_browser.cjs)
documents the test-server environment variables needed to repeat these checks.

Real phones, the intended classroom network and manual accessibility acceptance
remain covered by the [classroom device checklist](../../docs/classroom-device-checklist.md).
No original repository, existing course or private media was changed.
