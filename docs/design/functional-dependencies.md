# Functional Dependencies and Keys Lab

Current integration, 2026-11-07: FD Lab 0.5.0 uses manifest revision 4, state
schema 3, typed `SaveActor` records (25 summaries per page) and host-owned
`SetCredit` / `PublishPoints` scoring. The old `ActorTransition` API is no longer
used by this candidate. Host pin: `7b9934d91f3affcc54e2ab6573c8c662cc87348a`.
See the [integration and scoring record](functional-dependencies-points-validation.md)
and [points guide](../fd-lesson.md#awarding-points). The earlier development and
capacity history below describes its original versions; those timings do not
establish performance for this integration. Engine seed/answer/result formats
remain v1. Upgrades require new bundles and sessions.

Status: F1 engine and F2/F3 prepared classroom modes implemented locally, 2026-11-06.
The [package](../../plugins/fd-lab/README.md) supplies reasoning for all three modes
and classroom editors for all three modes. See the [English guide](../fd-lesson.md),
[German guide](../fd-lesson-de.md) and [F3 validation](functional-dependencies-f3-validation.md).
Physical-phone, load and release gates remain separate work. The [implementation plan](functional-dependencies-plan.md),
[draft contract](functional-dependencies-contract.md) and
[checked examples](functional-dependencies/README.md) make the next work concrete.
Reviewed against local host commit `de33515` and collection commit `5f00b62`.

The 2026-11-07 integration is implemented in FD Lab 0.5.0 with state
schema 3. See the [current contract](functional-dependencies-contract.md) and
[integration record](functional-dependencies-points-validation.md).
The original domain design below remains applicable; storage capacity and
measured feedback throughput are separate claims.

## Purpose and teaching sequence

Help students explain what follows from a stated set of functional dependencies
(FDs), and why a proposed key is or is not a candidate key. The activity supplies
small schemas with explicit business assumptions. It does not guess constraints
from column names or treat uniqueness in one sample table as a schema guarantee.

The classroom activity has three modes, presented as a short sequence:

| Mode | Student action | Evidence of success |
| --- | --- | --- |
| Attribute closure | Start from the given set, apply displayed FDs step by step, and submit the resulting set | Every step is applicable and productive; the reached set and submitted closure are the complete closure |
| Candidate keys | Assemble one key or a collection of all keys, as requested | Each submitted set determines the whole relation and is inclusion-minimal; all-keys mode also checks completeness |
| FD implication | Decide whether a target FD follows; construct a derivation or a two-row counterexample | A checked derivation reaches the target, or the rows satisfy every given FD and violate the target |

The starting set in an assessed closure task is fixed by the author. A presenter
may explore other sets in an explicitly labelled demonstration; doing so does
not change the exercise or saved answers. Practice feedback is optional; the
default withholds mathematical feedback until the presenter reveals it.

Normal forms, decomposition, dependency preservation, minimal covers, discovery
from data, SQL UNIQUE/NULL semantics, multivalued dependencies and arbitrary
Armstrong-proof editing are outside v1. Minimal-cover and decomposition lessons
can later reuse the engine through a declared evaluation binding. This package
must not depend on the relational-algebra or transaction provider to work.

## Worked classroom example

Use a workshop booking relation with these deliberately simplified assumptions:

| Symbol | Meaning | Assumption |
| --- | --- | --- |
| P | Person identifier | Each person has exactly one registered email |
| E | Email | Each registered email belongs to one person |
| W | Workshop | Each workshop has one tutor and one room |
| T | Tutor | A tutor can teach several workshops |
| R | Room identifier | Each room belongs to one building |
| B | Building | A building can contain several rooms |

Given `P → E`, `E → P`, `W → TR`, `R → B`, start with `W`.
Applying `W → TR`, then `R → B`, gives `W+ = {W,T,R,B}`. It does not
give a person or email. The two candidate keys are `{P,W}` and `{E,W}`.
`{P,E,W}` determines everything but contains a redundant attribute;
`{P,T}` does not determine the workshop. `{P,W}` is a valid answer to
“find one key”, but incomplete for “find all keys”.

For implication, `W → B` follows by a derivation. `T → W` does not.
A counterexample can hold the tutor equal in two rows while changing all
other attributes. It satisfies every given FD and violates `T → W`.
This is a logical construction using symbolic values, not invented real bookings.

The [example sources](functional-dependencies/examples.json) include this
sequence in English and German, a schema with keys of different sizes, a schema
without FDs, and an empty key. These are public synthetic teaching examples.
An author's worked answer is kept private by the eventual preparation process.

## Mathematical decisions

An FD constrains all legal instances, whereas a particular table can satisfy an
additional FD accidentally. Closure tests implication. Candidate keys are
inclusion-minimal superkeys, not necessarily keys of minimum cardinality; choosing
a primary key is a separate design decision. These definitions follow
[Database System Concepts, chapter 7](https://www.db-book.com/slides-dir/PDF-dir/ch7.pdf).
The distinction between derivation and a legal counterexample also appears in
[Waterloo's FD exercises](https://cs.uwaterloo.ca/~tozsu/courses/cs448/assignments/a3sol.htm).

The following are the plugin's proposed operational rules:

- One relation, one to eight distinct attributes, zero to 24 FDs. Attribute sets
  may be empty. A right side must be nonempty; a left side may be empty.
  Multi-attribute right sides, trivial FDs, redundant FDs and cycles are legal.
- Closure starts at X and repeatedly adds an FD's right side when its entire
  left side is already known. A full pass without additions ends the process.
  Cycles terminate because attributes are only added. No reverse implication
  is inferred from an arrow, and a composite determinant requires all its members.
- A student derivation references the displayed FDs. Each accepted step adds at
  least one attribute; there are at most eight productive steps. Different
  valid orders are accepted. A no-op receives “already known”, rather than
  pretending to be a useful proof step. The UI supports undo.
- A set K is a candidate key when its closure is the entire relation and removing
  any single member loses that property. Single removals suffice by monotonicity:
  any smaller superkey would be contained in a single-removal subset.
- Enumerate all at most 256 subsets, cache their closures, and select minimal
  superkeys. This gives exact completeness within the declared bounds. It
  handles cycles and differently sized keys without heuristic pruning mistakes.
  The UI must distinguish an empty answer `[]` from the collection `[∅]`.
- For a negative implication claim, students choose which columns agree across
  two symbolic rows. Let C be that agreement set. Every given `L → R` must have
  either `L` not contained in C or `R` contained in C; the target must have its
  left side contained in C and some right-side attribute outside C.
  This checks an actual countermodel. No-match on sample data is not a proof.
- A guaranteed witness for a non-implied `X → Y` agrees exactly on X's closure:
  row 0 has symbol 0 everywhere; row 1 has 0 in that closure and 1 elsewhere.
  Closure ensures every premise FD is satisfied, while a missing target attribute
  violates the target. Positive implications cannot have such a witness.

The independent checker compares the forward algorithm with intersection of all
closed attribute sets, checks tiny FD theories exhaustively, and validates
counterexamples by comparing the actual row values. This is design evidence,
not a browser implementation or a proof of runtime conformance.

## Phone, presenter and projector

The normal phone interface uses attribute buttons, FD cards and short lists;
students never need to enter bit masks or JSON. At 320 px, use a vertical layout,
wrapped sets and labelled controls with at least 44 px touch targets. All actions
must work with keyboard and visible focus. Do not rely on dragging, colour alone,
hover, or a dependency graph to explain a composite determinant.

For closure, show “known attributes”, the FD list, an undoable step history and
a final-set selector. In assessment mode, the local interface only checks input
shape; “Check step” and computed highlights belong to practice/demonstration
mode. In key mode, select attributes, add a proposed key, and remove or edit
entries. Do not show the expected number of keys before feedback release.
For implication, provide “follows” with a derivation builder, or “does not follow”
with same/different toggles for the two-row witness. A partial edit is a draft.

Saving an answer is explicit. Show draft, saved/pending, evaluated/withheld,
feedback available and unavailable states distinctly. Preserve focus, selections
and drafts across other students' answers. A newer answer from another device
or a reset offers “load saved answer” or “keep draft”; never silently resubmit.
Use structured dispatch errors and preserve work on queue/worker failures.

The presenter opens/closes submissions, reveals the worked solution, inspects
one answer at a time and optionally shares it anonymously. A live demonstration
can step through the prepared worked proof or inspect a selected key; it uses
the same semantics. The projector keeps the static exercise visible initially,
then shows the deliberately selected demonstration, worked answer or anonymous
response. Public demonstrations and sharing are enabled only after reveal;
private presenter inspection is available earlier. Practice feedback stays on
the submitting student's device. Aggregate submission counts are separate from correctness.
Wrong answers should be explainable, not turned into a public leaderboard.

## Feedback and classroom state

| Condition | Useful released feedback |
| --- | --- |
| FD used too early | Which determinant attributes were missing at that step |
| Repeated or unproductive step | This FD adds no new attributes here |
| Closure incomplete | Which attributes are still derivable, with one next applicable FD |
| Closure overclaimed | Which claimed attributes cannot follow from the starting set |
| Not a superkey | Which attributes its closure does not reach |
| Superkey, not candidate key | One removable attribute and the reduced set's closure |
| Incomplete list of keys | Some keys are missing; reveal may list the full answer |
| False positive implication | A legal two-row counterexample after release |
| Invalid negative witness | The violated premise FD, or why the target still holds |
| Runtime unavailable | Saved answer is pending or needs retry; never “incorrect” |

The content type grades mathematical facts; the engine supplies them without a
grade. Canonical equality with the author's chosen answer is never the success
criterion. A positive implication may need only a prefix of a full closure
derivation. Full closure tasks require completion; the two goals differ.

Use introduce/open/closed/revealed phases, a presenter control version and a
separate answer version per authenticated actor. Accept replacements while open;
close rejects new submissions but lets accepted evaluations finish. Revealing
closes submissions, releases the worked solution and permits late accepted
results to update feedback. Reopening hides the UI solution but cannot make an
already disclosed answer secret. Reset starts a new epoch and cancels old work.

Keep one current answer and compact feedback per actor. Schedule evaluation with
SDK `Evaluate`/`CancelEvaluation`, and verify epoch, correlation, complete binding,
exercise identity, answer identity and mode before accepting results. Exact
mathematical facts must agree with independently prepared closure/key tables;
check trace and witness certificates as well. Stale or inconsistent results do
not overwrite current feedback. No private queue, routes or host database tables.

## Privacy and authoring

Public data contains the complete schema, FDs, task, business assumptions,
localized text and UI policy. There are no hidden FDs that could make a student's
reasoning unknowably wrong. Private preparation holds the worked answer,
explanation, independent closure/key tables and engine bindings. Roles receive
only the projection needed: a participant's own answer and permitted feedback,
aggregate projector counts, or selected presenter inspection. Sharing is explicit
and strips actor identity. Reveal releases selected solution material, not the
entire private preparation or binding. Public FDs make solutions computable;
withholding answer files is not an anti-cheating guarantee.

The proposed distribution `texstage-fd-lab` contains an engine and a content
type, with optional style `texstage-fd-lab.sty`. The style only wraps the generic
prepared-item bridge; it neither implements reasoning nor installs code.
One JSON lesson produces the live activity, handout exercise and worked solution.

Proposed author syntax (not yet runnable):

```tex
\usepackage{texstage}
\usepackage{texstage-fd-lab}
\begin{frame}{Which attributes does a workshop determine?}
  \fdlab{workshop-closure}{.94\linewidth}{.65\textheight}
\end{frame}
```

```json
{"format":1,"language":"en","items":[
  {"id":"workshop-closure","type":"io.github.stefanjdecker.fdlab.exercise",
   "source":"activities/workshop-closure.json"}
]}
```

The sidecar source path is relative to the master deck directory and remains
confined beneath it. The authoring hook validates the worked answer using an
independent Python model before generating escaped TeX fragments. Invalid
solutions stop the build. Exercise PDFs show the problem and writing space;
solution PDFs show a step table, key minimality argument, or checked witness.
Keep generated fragments local; distribute only intended exports. Existing
courses and style snapshots require no changes for design or implementation.

## Ownership and host review

The provider owns FD algorithms, semantics, schemas, feedback, lesson phases,
renderers, translations and style. TeXStage continues to own authentication,
roles, persistence, epochs, receipts, job supervision, evaluator policy,
mount lifecycle and the prepared-authoring bridge. Lecture-tools-next needs
no FD-specific conversion or compilation logic.

The current experimental host already has the required typed facts, prepared
authoring, structured command errors, reset, mount reconciliation and atomic
queue replacement. No new domain-specific SDK mechanism is proposed. In
particular, this lesson does not depend on the relational visual editor or the
unfinished transaction lesson. Browser security is unchanged; provider engine
entries must be self-contained worker modules. Classroom throughput and a
published compatible host pin remain gates, not assumed capabilities.

The [plan](functional-dependencies-plan.md) specifies package files, independent
verification, implementation order and measurable exit criteria.
