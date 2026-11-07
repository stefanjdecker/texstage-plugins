# Query-plan Challenge

Version 0.7.0 uses the quiz system's speed points and shared streak bonuses.
Set `"points": 1000` for the base reward and `"time": 120` for the speed window
in seconds, or omit points / use `0` for practice. Points appear on reveal;
reset withdraws the award and recalculates later streak bonuses. See [points and feedback](../../docs/query-plan-points.md).

Experimental TeXStage provider 0.7.0: physical-plan selectors on phones, local
cost inspection, prepared LaTeX exercises/solutions and verified classroom feedback.
Costs are teaching units, not execution time.

- Provider: io.github.stefanjdecker.queryplan
- Engine: io.github.stefanjdecker.queryplan.cost
- Prepared slide type: io.github.stefanjdecker.queryplan.challenge
- Style: texstage-queryplan-challenge.sty
- Command: \queryplanchallenge{item-id}{width}{height}

Start with the [classroom guide](../../docs/query-plan-lesson.md). It explains
student editing/estimation/submission, presenter controls, privacy, conflicts,
reset and model limits. The [authoring guide](../../docs/query-plan-authoring.md)
covers isolated installation, explicit enablement, the complete source format,
LaTeX and static exports. No existing course environment or pin changes implicitly.

One source supplies the public query/statistics/baseline, private reference and
worked explanation, and all static editions. Before sharing/reveal, the projector
retains the exercise. The phone editor never receives private answers before reveal.

Use a fresh environment with the matching TeXStage development wheel and its
locked development dependencies:

```sh
python maintenance/build_wheels.py --package query-plan
python -m pip install --no-deps dist/texstage_query_plan-0.7.0-py3-none-any.whl
texstage plugins --data ./query-plan-profile inspect io.github.stefanjdecker.queryplan
texstage plugins --data ./query-plan-profile enable io.github.stefanjdecker.queryplan --version 0.7.0 --payload <displayed-payload>
texstage build examples/query-plan/lesson.tex --activities examples/query-plan/lesson.activities.json --data ./query-plan-profile --key local-demo-key -o artifacts/query-plan-lesson
python -m pytest plugins/query-plan/tests -q
python maintenance/query_plan_probe.py --output artifacts/query-plan-engine
python maintenance/query_plan_authoring_probe.py --output artifacts/query-plan-authoring
```

The authoring probe needs pdfLaTeX/latexmk and a new output directory.
For actual browser interaction run maintenance/query_plan_ui_browser.cjs with
the built bundle and a result directory; set PYTHON to the isolated environment.
The separate query_plan_state_browser.cjs tests protocol races and
query_plan_browser.cjs tests the engine and active worker restrictions.
Use the collection's locked Playwright package and select BROWSER=chromium,
firefox or webkit. A Chromium channel override applies only to Chromium.

The [Q4 record](../../docs/design/query-plan-ui-validation.md) identifies the tested
artifact. Q0–Q3 evidence remains milestone history. The engine and cost formulas remain unchanged. Version 0.7.0 uses manifest
revision 5, state schema 5, per-student records and a 25-answer presenter page. The new resource payload
requires explicit reviewed enablement; do not hand-edit old deck pins.

Only maintainers need Node to regenerate the self-contained engine worker.
The UI uses provider-owned modular resources and bounded local estimation;
it does not run an optimizer or call the private evaluator binding for preview.
Worker security restrictions remain unchanged. State/view schemas are generated
by maintenance/build_query_plan_lesson_schemas.py.

The [points validation](../../docs/design/query-plan-quiz-points-validation.md) records
the checks rerun on 0.7.0; the [600-student milestone](../../docs/design/query-plan-600-validation.md)
is historical 0.5.0 evidence. The matching 0.2.1.dev6 host is required;
rebuild the bundle and start a new session.

The historical [Q5 record](../../docs/design/query-plan-release-validation.md) adds measured
64-participant load, evaluator recovery and Windows/Linux artifact checks.
The [release procedure](../../docs/query-plan-release-checks.md) covers the new
CI workflow and manual gates. Physical-phone LAN and screen-reader checks,
successful hosted jobs and a published compatible host pin remain pending.
This is a local candidate, not a catalog publication. A style or activity upload
never installs code.
