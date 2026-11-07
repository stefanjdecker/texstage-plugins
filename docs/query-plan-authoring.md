# Authoring Query-plan Challenge lessons

Optional game points are described in [points and feedback](query-plan-points.md).
The four examples use 1,000 base points and a 120-second speed window, with quiz streak bonuses. Existing sources without
a `points` field remain unscored when rebuilt.

Version 0.7.0 adds quiz speed/streak scoring and retains per-student storage and a paginated presenter roster. One JSON lesson source produces a
prepared TeXStage slide, a student exercise, a worked solution and static exports.
The independent cost engine from 0.1.0 is unchanged. This is an experimental
development package, not a published plugin-catalog release.

Students can solve the printed exercises or use labeled phone selectors,
inspect local costs and submit a plan. Presenter controls open/close answers,
inspect and anonymously share submissions, reveal solutions and reset.
See the [classroom guide](query-plan-lesson.md),
[classroom contract](design/query-plan-classroom-contract.md) and
[current validation record](design/query-plan-quiz-points-validation.md).

## Install in a separate development environment

Use Python 3.12 or newer, a compatible development TeXStage wheel, and TeX Live
with pdfLaTeX, latexmk, Beamer, babel (English/German), tabularx and adjustbox.
The [validation record](design/query-plan-quiz-points-validation.md) identifies
the exact tested host and provider. The version number 0.2.1.dev6 alone is not a
sufficient host pin. Obtain/build the approved development wheel before installing
this plugin; do not assume an older public host provides these APIs.
Build from a clean checkout: the wheel helper deliberately rejects mixed
versions in a package's generated dist directory.

From the collection root, create an isolated environment and install the host's
locked dependencies (the sibling host checkout supplies requirements/dev.txt
and requirements/build.txt), followed by the approved host wheel. For example,
in PowerShell:

```powershell
python -m venv artifacts/query-plan-env
.\artifacts\query-plan-env\Scripts\Activate.ps1
python -m pip install --require-hashes --only-binary=:all: -r ../texstage-public/requirements/dev.txt -r ../texstage-public/requirements/build.txt
python -m pip install --no-deps <approved-host-wheel>
python maintenance/build_wheels.py --package query-plan
python -m pip install --no-deps dist/texstage_query_plan-0.7.0-py3-none-any.whl
texstage plugins --data artifacts/query-plan-profile inspect io.github.stefanjdecker.queryplan
```

Replace `<approved-host-wheel>` with its path. After reviewing the inspection
output, replace `<payload>` below with the displayed SHA-256 provider payload:

```powershell
texstage plugins --data artifacts/query-plan-profile enable io.github.stefanjdecker.queryplan --version 0.7.0 --payload <payload>
texstage build examples/query-plan/lesson.tex --activities examples/query-plan/lesson.activities.json --data artifacts/query-plan-profile --key local-demo-key -o artifacts/query-plan-lesson
```

These commands affect only the new environment and profile. Installing a wheel
does not enable it, and uploading a deck never installs code. Do not reuse an
existing course profile for development. Version/payload pins from 0.1.0 must be
explicitly reviewed and replaced in a new profile for this 0.7.0 capability.

The build emits a live lesson bundle, the stage PDF, a static PowerPoint and
a checked solutions PDF under the output's build directory. Static PowerPoint
contains the exercise slides, without worked answers or presenter notes.
To reproduce all editions, including handout and direct pdfLaTeX checks:

```powershell
python maintenance/query_plan_authoring_probe.py --output artifacts/query-plan-editions
```

The output directory must be new. Its report.json lists the exact generated
paths and provider identity. Build artifacts are disposable; source files stay
under examples/query-plan.

## Three author-owned files

1. A normal LaTeX deck defines titles, teaching context and activity placement.
2. An explicit activity sidecar maps each stable ID to its source JSON.
3. Each lesson JSON contains the fixed query/statistics, starting plan, goal,
   worked answer and English/German explanation.

The [example deck](../examples/query-plan/lesson.tex) demonstrates four exercises:

| ID | Question | Starting cost | Minimum |
| --- | --- | ---: | ---: |
| selective | Is an index useful for ten matches? | 20000 | 5210 |
| broad | Is the index useful for 5000 matches? | 2006200 | 20000 |
| library | Which join order avoids unnecessary work? | 128280 | 116430 |
| memory | What changes with 1024 bytes of hash workspace? | 259310 | 214330 |

These are teaching units, not database execution times. The library query
returns one occurrence per qualifying loan; names may repeat. Relational Algebra
Lab studies logical trees with set semantics. Their answers and metrics are not
interchangeable.

### LaTeX

```latex
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{texstage}
\usepackage{texstage-queryplan-challenge}

\begin{frame}{Few matches: should we use the index?}
  \queryplanchallenge{selective}{.97\linewidth}{.82\textheight}
\end{frame}
```

`\queryplanchallenge{id}{width}{height}` delegates to the host's
`\texstageprepared` command. ID must match the sidecar. Width and height are TeX
dimensions for the registered activity rectangle. The generated text fits within
that rectangle, scaling down when necessary. Use a full frame, short identifiers
and concise explanations; a schema-valid 2000-character explanation is not a
readable slide. Put longer teaching notes on separate frames.

The thin style contains no cost logic. It loads texstage, tabularx and adjustbox.
Preparation calculates all facts once; TeX renders the appropriate fragment and
does not run Python or compute reference answers.

### Activity sidecar

```json
{
  "format": 1,
  "language": "en",
  "items": [
    {
      "id": "selective",
      "type": "io.github.stefanjdecker.queryplan.challenge",
      "source": "activities/selective.json"
    }
  ]
}
```

Paths are relative to the master deck directory, not the sidecar directory.
Sources must remain inside that directory; absolute paths, traversal and escaping
links are rejected by the host. Pass --activities explicitly. Use language "de"
for German generated labels/explanations; authored frame titles remain your text.

### Lesson source and cost rules

Start by copying [selective.json](../examples/query-plan/activities/selective.json)
or the three-relation [library.json](../examples/query-plan/activities/library.json).
The exact fields and limits are specified by the
[frozen contract](design/query-plan-challenge-contract.md):

- `format: 1` and `exercise`: fixed query, relation/column types, available
  equality indexes, base statistics, all connected-subset row estimates and
  hash workspace limit.
- `baseline`: a feasible starting physical plan.
- `goal`: `{"kind":"best"}` or `{"kind":"budget","max_cost":130000}`.
- `worked_answer`: any feasible plan satisfying that goal.
- `explanation`: plain-text `en` and `de` strings.
- Optional `points`: base reward from 0 to 10,000; omitted or zero means practice.
- Optional `time`: speed window from 1 to 3,600 seconds, default 120. It does not
  automatically close answers. See [speed and streak rules](query-plan-points.md).

The source permits one to three relations. Plans use sequential/index scans and
nested/hash joins. JSON node references are zero-based canonical postorder;
printed plans number nodes from one. Filters and joins are fixed, not editable
SQL. The displayed query lists outputs, equality joins and filters. Filter
literals use JSON notation, including quoted strings and true/false.

All printed cost formulas use the exposed estimates. Sequential scans cost
100P+N; index scans cost 400(H+R)+R; nested joins cost LR+O; hash joins cost
2B+Q+O. Hashing requires B(W+16) bytes for that operator's build side. Joined
widths add. Add child totals once; summing every displayed subtree total would
double-count work. The optimum is exhaustively checked within the bounded legal
plan family (at most 864 candidates).

An infeasible baseline, unreachable budget or unsuitable worked answer fails
preparation. A best goal accepts every tied optimum. A budget solution may be
nonoptimal; the solution then prints both its worked plan and an optimal
reference. Changing the baseline cannot change the optimum.

## Editions, privacy and freshness

The exercise contains the query, complete statistics, cost rules, memory limit,
goal and starting plan with its cost. The solution replaces the starting plan
with the worked plan, explanation, computed minimum and tie count.

Public deck data contains the normalized exercise, baseline and its analysis,
and visible goal. Worked answers, explanations, reference facts and evaluation
bindings are private bundle data. The presenter may inspect references and a
selected answer privately. Participant/projector views withhold the worked
solution, optimum and correctness until explicit reveal. Anonymous sharing
releases only the chosen plan. The participant surface renders the selector editor from public problem data and the actor's own view.

Treat the local source JSON, generated solutions, prepared directory and complete
instructor bundle (including keys.json) as teacher material. Distribute the student
handout or static PowerPoint when solutions should remain private. The host does
not serve keys.json as a public bundle file. This boundary does not hide the public
statistics: learners can independently find the optimum.

To obtain direct pdfLaTeX entry points:

```powershell
texstage prepare examples/query-plan/lesson.tex --activities examples/query-plan/lesson.activities.json --data artifacts/query-plan-profile -o artifacts/query-plan-prepared
```

The command prints paths for present, handout and solutions entry points. Compile
the selected generated file with pdfLaTeX twice. Keep the generated directory,
source deck and approved installed provider available at their recorded locations.
These are local exports, not portable source archives. Source/provider edits
invalidate the export with “Stale prepared input”; rerun prepare/build to refresh
the facts and identities. Never edit generated fragments to change a lesson.

Author text is escaped rather than interpreted as TeX. The standard pdfLaTeX/T1
output supports the documented Latin repertoire in the examples; other Unicode
in explanations is printed explicitly as [U+XXXX]. Filter literals use escaped
JSON notation. Full original explanation text remains in private prepared data.
Long uninterrupted strings gain safe line-break opportunities.

## Verify or extend

Run `python -m pytest plugins/query-plan/tests -q` in the isolated installed-wheel
environment. Tests cover the engine, authoring, real exports, privacy, language,
maximum-size worker preparation, source confinement and stale exports.
The [Q2 evidence](design/query-plan-authoring-validation.md) also records visual
PDF review and real-host Chrome/Firefox/WebKit navigation checks.

Maintainers can run `maintenance/query_plan_authoring_browser.cjs` with the built
bundle and a new result directory. Set PYTHON to the isolated environment and
BROWSER to chromium, firefox or webkit; set TEXSTAGE_BROWSER_CHANNEL=chrome only
for an installed Chrome. The helper serves a disposable loopback session.
The separate cost-engine browser probe retains the existing restrictive worker CSP.

The classroom implements bounded learner state, independent server checks, retries,
explicit sharing, irreversible reveal and reset. Version 0.7.0 uses manifest
revision 5 and state schema 5: answers live in host-owned records, and presenter
roster pages contain at most 25 summaries. Install the matching host, explicitly
enable the new provider payload, rebuild the bundle and create a new session.
Keep existing sessions in their original environment; there is no automatic
state migration. See the
[implementation plan](design/query-plan-challenge-plan.md).
