# Normalization Workshop: plugin design

Status: N1–N3 and the N4 comparison/evidence slice implemented locally.
The [workshop guide](../normalization-workshop.md),
[N4 validation record](normalization-workshop-n4-validation.md) and
[discussion contract](normalization-workshop-discussion-contract.md) describe
the 0.3.0 discussion implementation. The
[0.3.1 accessibility record](normalization-workshop-accessibility-validation.md)
adds keyboard, German and native zoom evidence. The
[current capacity record](normalization-workshop-600-validation.md) describes
version 0.4.0: a 600-student target, 1,000 saved-answer ceiling, scoped records and
16-entry presenter pages. The previous
[64-participant measurements](normalization-workshop-webkit-validation.md)
remain historical evidence. Engine and authoring semantics are unchanged.
Full usability and N5/N6 classroom/release gates
below remain target behavior. See the [implementation plan](normalization-workshop-plan.md),
[frozen v1 contract](normalization-workshop-contract.md) and
[synthetic examples](normalization-workshop/README.md).

## Purpose and first release

Students learn to justify a schema design: what determines what, which attribute
sets identify a tuple, and what is preserved when a relation is decomposed.
Feedback explains a failed property instead of merely comparing against the
teacher's preferred table names.

V1 assesses 2NF/3NF/BCNF classification and arbitrary bounded decompositions.
It computes functional-dependency (FD) closures, all candidate keys and prime
attributes internally to explain and verify those tasks. A decomposition receives separate results for attribute coverage,
each component's normal form, lossless join, and dependency preservation.
The assumed relational model has atomic values and set semantics; 1NF is an
explicit assumption, not something inferred from a schema diagram or checked by
this engine. There are no NULLs, SQL bag semantics or empirical FD discovery.

The distinction between schema constraints and observed data is central.
An example table can refute a claimed FD, but agreement on a few rows does not
establish that it holds for every legal instance. The workshop states the business
rules explicitly. See [Waterloo's dependency model](https://cs.uwaterloo.ca/~david/cs348/handout-FD.pdf).

Out of scope for v1: MVDs/4NF/5NF, inclusion dependencies and foreign-key
inference, SQL DDL generation or execution, database import, automatic grading of
free-text explanations, and editing minimal covers or grading synthesis steps.
A worked 3NF decomposition is checked by its properties; the first release need
not implement a student-facing synthesis algorithm. Sample data is illustrative,
not the grading oracle.

## A coherent first lesson

Use a fictional one-term course-registration table:

| Attribute | Meaning |
| --- | --- |
| S | Student identifier |
| N | Student name; names are not unique |
| C | Course identifier |
| T | Course title |
| I | Instructor identifier |
| O | Instructor office |

Business rules: S -> N; C -> T,I; I -> O. Each course has one instructor
during this term; an instructor may teach several courses. Registration is one
tuple per student/course pair. SC is the only candidate key.

1. **Why split the table?** Discuss a repeated office and the risk of updating
   only one occurrence. The static slide states all business assumptions.
2. **Closure warm-up:** discuss C and predict C+ = CTIO. Reveal a step-by-step FD
   application, including I -> O. C still does not identify the student.
3. **Key warm-up:** propose SC and explain minimality: removing S loses S,N; removing C
   loses C,T,I,O. A larger superkey is not a candidate key.
4. **Diagnosis:** classify the original as 1NF only. S -> N is already a
   partial dependency on the composite key.
5. **Repair:** propose SN, CTI, IO, SC. All components are BCNF; the
   decomposition is lossless and preserves the stated FDs. Accept other
   decompositions meeting the same published criteria.
6. **Compare:** remove SC to get SN, CTI, IO. All attributes remain, every
   component is BCNF and every FD is preserved, but the join is lossy: student/
   course associations were discarded. Show a checked counterexample.
7. **Trade-off:** use Booking(Student, Topic, Tutor), with Student,Topic -> Tutor
   and Tutor -> Topic. Assume one tutor per student's topic and one topic per
   tutor. Keys are Student,Topic and Student,Tutor: the original is 3NF, but
   Tutor -> Topic violates BCNF. Splitting into Tutor,Topic and Student,Tutor
   is lossless and BCNF, yet loses preservation of Student,Topic -> Tutor.

The assessed diagnosis/repair tasks are distinct activity items sharing an
authored scenario, not one mutable cross-slide wizard. Each item has its own
answer, phase and epoch. Closure/key warm-ups are static discussions in the
standalone deck; an optional combined deck uses FD Lab for those interactions. Reusing the
scenario means reusing author data, not depending on a previous student's answer.
The progression can be shortened or reordered by the lecturer.

For the trade-off, the presenter shows two defensible choices: retain the 3NF
relation for local enforcement of the FDs, or choose the BCNF decomposition and
recognize that the lost constraint needs additional enforcement. BCNF is not a
promise of dependency preservation. The definitions and this distinction follow
[Database System Concepts, chapter 7](https://www.db-book.com/slides-dir/PDF-dir/ch7.pdf);
the fictional lesson and interface are this proposal.

## Phone, presenter and projector

Use two fixed task modes: `classify` and `decompose`.
The task is selected by the author, never by a submitted answer.

- **Phone:** show the task and a collapsible FD list. Students use labeled
  attribute chips with checkboxes, Add relation, Remove and Undo.
  Decompositions are stacked cards; no dragging, tiny canvas or JSON entry is
  required. Classification offers named forms and a determinant/dependent
  selector for a witness. The empty set has an explicit control.
- **Before submission:** check only syntax, duplicate cards and missing inputs.
  Do not display authoritative closures or solution hints during the default
  attempt. Preserve partially edited cards and focus across class updates.
- **Submission:** a deliberate Submit saves a version and queues evaluation.
  Show Saved / Waiting / Checked (feedback withheld) / Unavailable separately.
  Edits remain possible while open; only a new Submit replaces the saved answer.
- **Presenter:** open, close, reopen before reveal, inspect a selected answer,
  explicitly share/unshare it anonymously, then reveal. Counts distinguish
  received, pending, checked and unavailable. An answer is not wrong merely
  because the evaluator is unavailable.
- **Projector:** retain the readable static task while students work. Share only
  the selected anonymous answer, with explicit discussion controls. After
  reveal, show property badges with words and an expandable explanation.
  Do not flood the projector with a full chase tableau.
- **Feedback:** show the student's own saved answer and diagnostics. For a
  lossy decomposition, offer a small legal relation and an extra joined tuple.
  For a lost FD, identify the FD and the failed projected-closure calculation.
  Explain “all components in BCNF” separately from “lossless” and “preserved.”

Classroom phases are introduce -> open -> closed -> revealed. Close retains
accepted pending work; late valid completions still update its results.
Closed -> open increments a phase guard; revealed -> open requires reset.
Navigation deactivates submission but retains durable answers.
Reset starts a fresh epoch and suppresses old jobs. If a newer same-actor answer
or reset arrives while editing, offer Reload saved / Keep draft; never
automatically resubmit. Unsaved drafts need not survive leaving the slide in v1.

At 320 CSS pixels, cards stay vertical, controls have text labels and generous
touch targets, math has a readable text equivalent, and color is supplementary.
Keyboard users can select attributes and manage cards without pointer gestures.
English and German strings belong in resources. Static handouts leave room for
working; solution pages show closures, keys, decomposition checks and reasoning.

## Mathematical decisions that prevent misleading feedback

Use F+ for implied dependencies, including dependencies projected onto a
component. Filtering only the originally written FDs is insufficient.
For a component U and X within U, its closure is closure_F(X) intersect U.
Minimal superkeys and prime attributes are computed for that component.

For each nontrivial X -> a implied on U, BCNF requires X to be a superkey;
3NF also permits a to be prime. 2NF forbids a non-prime attribute depending on
a proper subset of any candidate key. Check all candidate keys, not just one
chosen primary key. The bounded exhaustive definitions avoid shortcuts based
on phrases such as “no transitive arrows.”

The engine uses a terminating FD tableau chase to decide multiway losslessness.
The binary intersection test is an independent cross-check for two components;
it must not be extended to a collection by checking arbitrary pairs.
A saturated unsuccessful tableau supplies a counterexample, which is verified
before presentation. The FD-only chase is described in
[Chris Pollett's lecture](https://www.cs.sjsu.edu/faculty/pollett/157a.3.23f/Lec20230925.html).

Dependency preservation is checked against the union of the projected
dependencies. It does not require every written FD to fit verbatim into one
component. A missing implication and its saturated closure form the feedback.
The preservation definition is described in
[RPI's normalization notes](https://cs.rpi.edu/~sibel/csci4380/fall2026/lecture_notes/lecture6.html).
The frozen contract supplies deterministic encodings, bounds and algorithms.

An answer can be well-formed and mathematically unsuccessful. That is normal
feedback, distinct from malformed input, resource refusal or evaluator failure.
Do not use host reference-result equality (`matches`) as correctness: table
ordering, equivalent decompositions and different valid witnesses may differ.

## Relationship to FD Lab

The separate [FD Lab](functional-dependencies.md) owns interactive
closure derivations, one/all candidate-key tasks and FD implication proofs.
Normalization Workshop owns normal-form diagnosis and decomposition. Do not
build a second closure/key assessment UI here. FD Lab now has its own engine; its classroom UI remains a separate milestone.

A combined deck can place FD Lab warm-up items before normalization items, with
both providers explicitly installed and pinned. Each type owns its own state;
no cross-item answer sharing or automatic provider installation is required.
The standalone normalization deck uses static warm-up discussion slides and
therefore does not require FD Lab to be implemented first.

Normalization still needs closure/key calculations inside its analyzer to check
projected dependencies and normal forms. Do not queue a separate engine job for
each internal closure or import another provider's browser module. Keep this
small mathematical kernel owned and tested here initially; reuse semantic test
cases across the projects where their formats agree. If actual implementation
justifies a shared library, make it an explicit versioned build dependency bundled
into each worker, with independent conformance. That extraction is not a new
host API or a prerequisite imposed by this design.

## Package and core ownership

| Proposed name | Responsibility |
| --- | --- |
| `texstage-normalization-workshop` | One portable distribution |
| `io.github.stefanjdecker.normalizationworkshop` | Provider identity |
| `io.github.stefanjdecker.normalizationworkshop.analyze` | FD analysis engine |
| `io.github.stefanjdecker.normalizationworkshop.workshop` | Prepared lesson content type |
| `texstage-normalization-workshop.sty` | Optional approved style |
| `\normalizationworkshop{item}{width}{height}` | Thin `\texstageprepared` wrapper |

The distribution, provider and analyzer are implemented locally. The content
type and style names remain reserved; no catalog release is published. Manifest
revision 2, plugin API 1 and a declared typed result schema are used. One provider owns both
engine and lesson; it does not import transaction or relational plugin modules.
Shared host conventions do not require a new cross-provider library.

The **engine** owns mathematical parsing, normalization, closures, keys,
normal-form facts, decomposition checks and replayable evidence.
The **content type** owns authoring, task acceptance policy, phases, compact
per-actor state, role projections, UI and LaTeX resources.
The **core** continues to own authentication, command receipts, persistence,
epochs, job leases, result validation and mount lifecycle.

No normalization-specific route, database table, host renderer or lecture-tools
command is needed. Use the existing `PreparedAuthoring` pipeline and typed
`Evaluate`/`CancelEvaluation` effects. Explicitly enabled, payload-pinned
providers are still required; a deck, sidecar or style cannot install code.

## Authoring and privacy

One lesson source contains public business rules, fixed task policy, starter
answer, a private worked answer and bilingual explanation. Preparation validates
the source and independently checks the worked answer with the Python model.
Failure stops the build. It produces public lesson data, private worked facts,
one engine binding and exercise/solution TeX fragments from that source.

The schema and FDs are public: students may reason out the answer themselves.
Feedback withholding is a classroom pacing feature, not secrecy of mathematical
consequences. Keep worked answers, other students' answers and assessment
receipts out of participant/projector transport until the appropriate action.
The evaluator receives no student-chosen seed or policy. It needs no hidden
sample rows; the claims are about all instances satisfying the declared FDs.

The prepared sidecar follows current master-deck-relative confinement. The
style comes from the enabled provider. Build live/stage, handout, solutions and
static PowerPoint from the same source. Direct-pdfLaTeX exports remain local
prepared artifacts; private preparation directories are not student packages.

## Review of the plugin system

The current host can express this activity without new API features. This design
particularly exercises compact mathematical facts, several valid answers,
explicit disclosure, and per-item phases. Reuse patterns from relational-lab,
not its query-tree assumptions or limits.

Required verification remains: worker startup and CSP in Chromium, Firefox and
WebKit; both schema validators; error codes and pending recovery; same-actor
conflicts, queue replacement and reset; authoring freshness and static layout.
Keep `connect-src 'none'` and the existing worker policy. Ship a generated,
self-contained engine worker and a portable wheel; end users need no Node build.

Budget or scheduling failures are findings to resolve, not permission to raise
core limits. Reduce provider limits or split a lesson into independent items
first. If a generic host defect is found, fix and regress it in Texstage
separately; never put FD rules into the host. See the plan for measured release
gates and the explicit boundary between design checks and a usable release.
