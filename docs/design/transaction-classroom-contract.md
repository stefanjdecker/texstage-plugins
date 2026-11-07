# Transaction classroom contract, version 1

The standalone engine contract is unchanged. The activity uses manifest 3,
state schema 1 and provider `io.github.stefanjdecker.transactionactivity` with
content type `.schedule`. The engine binding `analysis` names
`io.github.stefanjdecker.transactionengine.schedule`. There is no plugin-specific
host route, scoring table or database execution capability.

## Prepared material

`lesson-v1.json` wraps the inventoried engine exercise schema, 2–3 independently
checked distinct acyclic worked orders, and an English/German explanation.
The exercise permits 2–3 transactions, 1–3 objects, twelve non-commit operations
and one terminal commit per transaction. Values start within ±1,000,000; a write
adds at most ±10,000 to a preceding read from its own transaction, or writes a
bounded constant. IDs are `[a-z][a-z0-9_]{0,11}`; transaction IDs are T1, T2, T3.
The independent Python model checks structure and semantics, replays remembered
reads and derives direct conflicts. It enumerates certificates over at most three
vertices instead of relying on the worker's traversal implementation.

Public data is `{format, exercise}`. Private data contains original analysis and
worked explanations. Engine bindings are private. The full binding, including
engine key, is used in result namespaces; provider payloads and options are never
inferred from client messages. Live, handout, solutions and direct-LaTeX exports
share one preparation identity. Raw source changes invalidate preparation.

## Durable state and commands

The phase sequence is Ready → Predict → Inspect → Diagnose → Repair → Reveal.
Shared state contains phase/control tokens, cursor, monotonic prediction release,
active/paused flags, category counters, roster page, selected/shared snapshots and
a binding digest. It never contains the entire class's answers. Counters update
by subtracting the previous record's contribution and adding the replacement.

Each actor record contains epoch, overall version, and nullable `prediction`,
`diagnosis`, `repair` slots. Slots hold answer version, answer, status and private
feedback. Repair slots also hold correlation identity. SaveActor effects, job
cancellation/evaluation and the command receipt commit atomically. Each schema
closes objects and bounds collections; integer fields reject booleans.

| Message | Role | Guard / payload |
| --- | --- | --- |
| submit-prediction | participant | phase_token, answer_version, values per object |
| submit-diagnosis | participant | phase_token, answer_version, edges+witnesses, certificate |
| submit-repair | participant | phase_token, answer_version, complete legal order |
| retry-analysis | participant | phase_token, unchanged answer_version |
| advance-phase / resume-phase | presenter | control_version |
| seek-step | presenter | control_version, cursor |
| roster-page | presenter | control_version, page |
| select-answer / share-answer | presenter | control_version, actor, record_version |
| clear-share | presenter | control_version |
| _reset | presenter, host built-in | epoch and receipt guards |

Authenticated actor identity comes from the host. Participant messages cannot
select another actor. Presenter selection declares `record_actor_field`; it reads
one record and a bounded roster page. Operation/program-order errors are immediate
structural feedback; incorrect conflicts and witnesses are withheld until Reveal.

Navigation pauses open answers and changes phase/control tokens. Reset erases
records, advances epoch and cancels old work. Results require matching actor,
epoch, binding and correlation. Replaced results cannot change the current answer.
An accepted pending result can complete after closure. Independent verification
checks order, exercise identity, final values, remembered reads, trace, complete
direct edges and a valid (not necessarily identical) certificate. Failure stays
unavailable and can be retried without converting it into a wrong answer.

## Projection and feedback boundaries

Participant projection contains only its own filtered slots and public lesson
state; no peer counts, roster, selection, evaluation references or bindings.
Actor-only notification mode is safe because peer submissions do not change this
projection. Declared broadcast fields are phase, phase_token, active, paused,
cursor, prediction_revealed and shared. Cursor/phase/reveal updates reach everyone.

Prediction feedback releases at the last inspection step or on advancing beyond
Inspect. Diagnosis and repair feedback release in Reveal. Presenter controls can
inspect feedback privately before release. The projector never receives that
selection. Only an explicit Reveal-time anonymous share publishes a snapshot;
replacing that actor's answer clears it. Public exports call the ordinary validated
projector view; they do not redact a private archive. No points are emitted in v1.

Budgets: capacity 1,000 actors; 25 records/page; actor value 3,072 canonical ASCII
JSON bytes including a 512-byte pending feedback reserve; summary 256 bytes;
shared state 32 KiB; complete transition and role view 64 KiB. Existing engine
input/result limits and host 250-ms transition / two-second evaluation limits
remain unchanged. Those bounds are independent of classroom latency targets.

## Implemented surfaces

Participant input uses number fields, direct-edge checkboxes, witness and
certificate selectors, and operation cards with keyboard-accessible movement.
Drafts are preserved on peer updates. Same-actor conflicts offer explicit reload
or keep; neither sends automatically. Presenter controls guard phase transitions,
trace position, private inspection, sharing and reset. Presenter/projector overlays
show the problem, the current trace prefix and revealed explanations. All packaged
strings have English/German variants. The static exercise remains the fallback
when no live provider view can be mounted.
