# Query-plan classroom protocol v2 (0.5.0)

Version 0.7.0 extends this contract with optional [quiz speed points and shared
streak bonuses](../query-plan-points.md), manifest revision 5 and state schema 5.
It replaces 0.6.0's fixed rewards. Open/close/deactivation also control the host's
durable scoring clock; submission receipts preserve their accepted times. The
actor-record storage and cost model below remain unchanged. See the
[current scoring validation](query-plan-quiz-points-validation.md).

Content API 1, manifest revision 3, state schema 3. This supersedes the
0.3.0/0.4.0 classroom storage contract; the cost engine is unchanged.
The [engine/source contract](query-plan-challenge-contract.md) is unchanged.
This contract specifies the server protocol, actor records and projections. See
the [classroom guide](../query-plan-lesson.md) and
[0.5.0 capacity validation](query-plan-600-validation.md).
The static slide remains visible until a plan is shared or a solution revealed.

## State and commands

The state starts inactive in introduce, with zero phase/control versions, no
answers, no private selection and no shared demonstration. Activation enables
commands. Deactivation closes an open phase, advances phase/control tokens,
and clears the shared demonstration; it preserves saved answers and pending jobs.
Returning to the slide requires an explicit open. Revealed state stays revealed.

All declared messages use the host's latest revision policy. The host still
requires epoch, expected_revision and request_id in its normal command envelope.
It authenticates the actor and role, validates the closed payload schema, owns
receipts/reset/job leases and serializes transitions. Identity never comes from
a claimed actor field in a participant payload.

| Command | Role | Payload | Effect |
| --- | --- | --- | --- |
| submit-plan | Participant | phase, version, answer | Save/replace this actor's plan and queue analysis |
| open | Presenter | control | introduce/closed -> open |
| close | Presenter | control | open -> closed; pending results still arrive |
| reveal | Presenter | control | closed -> revealed; release solution/own feedback |
| select-answer | Presenter | control, actor (or null) | Select a version privately, or clear selection |
| share-selected | Presenter | control | In closed/revealed, project that selected version anonymously |
| clear-shared | Presenter | control | Remove the public demonstration |
| roster-page | Presenter | control, page (0–39) | Select an existing page of at most 25 summaries |
| _reset | Presenter, host-owned | empty object | New epoch, introduce phase, no answers/jobs/selection |

Open after reveal returns reset-required. Revealing cannot make information
secret again. Phase changes advance the phase token; each accepted presenter
control advances the control token. A submit requires the current open phase
and that actor's current answer version (zero when absent). It increments only
that answer version. Unrelated participants/results do not invalidate controls
or another actor's save.

Selecting records actor and version. Replacing that answer clears both private
selection and sharing. Open clears sharing. Public demonstrations contain only
the plan: no actor, roster number, answer version, result or correlation. Private
selection alone never projects anything. Participants never see other answers.

The host owns exact-request receipt replay. A second device submitting a different
request with an old answer version gets stale-answer. A second presenter using
an old control token gets stale-control. Old epochs cannot reset or modify a newer
attempt. Token counters saturate at 1,000,000,000 and require reset; navigation
can always close safely. There is no automatic resubmission or silent overwrite.

## Evaluation and assessment

The declared binding is analysis, using the prepared fixed exercise and cost
engine. Correlation is the SDK SHA-256 of actor/request/analysis. Replacing a
pending answer emits CancelEvaluation followed by Evaluate; the host commits
the replacement and queue accounting atomically.

Completion applies only to the pending slot matching actor, epoch, correlation
and binding. The host has already checked the lease generation, owner, namespace,
schema and complete outcome; the reducer additionally checks format/model and
exercise/answer identities. It independently runs the Python per-plan model
(at most five nodes) and compares the complete canonical facts, including
validity/reason, node order/coverage, subset masks, rows, widths, all local/subtree
costs and hash workspace. It never enumerates candidates in a reducer or view.

Only verified facts can produce:
- goal-met: feasible and equal to the prepared minimum, or within the public budget;
- target-missed: feasible but too costly;
- invalid: the exact verified feasibility reason and node;
- unavailable: operational failure or mismatched/malformed facts, without a grade.

Canonical equality with the worked answer is never assessment. Every tied optimum
passes best. A budget can accept a nonoptimal plan. A forged invalid result for a
valid plan is unavailable, not an incorrect grade.

Each host-owned actor record retains the plan, a stable roster number, answer
version/digest, epoch/correlation, status and compact
feedback. Full node traces are neither stored per actor nor exposed by these views.
Pending results may complete after close, reveal or navigation; replacements,
duplicate deliveries, cancelled old jobs and resets cannot overwrite newer work.
Lease expiry/retry, exhausted leases and restart delivery are host mechanisms.

## Role views and privacy

The generated closed portable schemas are under
[schemas/views](../../plugins/query-plan/texstage_query_plan/schemas/views).
All include phase, phase_version, active and answer count.

- Participant: only this actor's version/answer/status. Before reveal, feedback
  is absent. After reveal, compact goal/invalid/unavailable feedback appears;
  operational diagnostic details remain private.
- Presenter: control_version, aggregate pending/goal-met/target-missed/invalid/
  unavailable counts, page/pages and at most 25 roster summaries with
  actor/number/status, and explicitly
  selected answer with private diagnostics. Roster numbers follow first accepted
  submission and survive canonical persistence, replacement and new arrivals.
- Projector: no roster, selection, individual status or assessment counts.
- Presenter/projector may receive the explicitly shared anonymous plan.
- Presenter always receives the teacher solution. Participant/projector receive
  it only after reveal: worked_answer, optimal_answer, explanation (en/de),
  minimum and number of ties. A nonoptimal budget example therefore keeps its
  worked and optimal plans distinct.

No role view exposes evaluation bindings, digests/correlations, private source
envelopes, candidate lists or unrelated actors' answers. The public exercise
statistics remain sufficient for students to independently compute the optimum.
The host separately transports approved public exercise data and view epochs.

## Bounds and upgrade boundary

At most 1,000 distinct actors may save; the performance target is 600. Existing actors can replace at capacity.
Actor IDs have at most 256 code points and at most 1024 canonical ASCII JSON bytes;
these are authenticated host IDs, not display names. Oversized IDs are refused,
never truncated. A slot including its escaped actor key reserves at most 3072
bytes for the answer, metadata and maximum compact feedback before acceptance.

Shared state is limited to 16 KiB. Each actor value is bounded by the host's
4-KiB record limit, and its status summary by 512 bytes. The hook receives only
the current actor record (or the explicitly selected presenter target), never
the full class. Shared state contains counts and at most one selected/shared
snapshot. The save, counters, jobs and receipt commit atomically. Reset removes
the records and invalidates old jobs in the same transaction.

The complete transition remains below the host's
256-KiB cap, and each audience view below 128 KiB. Answer-v1's 1024-byte bound,
engine result bounds and preparation limits are unchanged. The worst-case tests
include escaped actor IDs, five-node plans, maximum versions/costs, bilingual
2000-character explanations, selection/sharing and evaluation effects.
Serialized capacity is not a measured classroom-throughput claim.

State schema 3 replaces the previous shared answer map. Provider version/payload pins
also change. Use a new enabled profile and new session/bundle. The host rejects
resuming an old session in a changed provider environment; no automatic in-place
state or course migration is provided.
