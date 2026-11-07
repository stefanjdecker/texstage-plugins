# Query-plan: 600-student scalability

Target: 600 individually authenticated students submitting in one activity, with
storage headroom for 1000. This milestone requires a new opt-in generic host
contract, not an increase to the old shared-state ceiling.

The candidate uses manifest revision 3, Query-plan 0.5.0 and state schema 3.
Each student's answer, version, correlation and compact feedback is stored in a
host-owned actor record. Shared state contains phase/control guards, aggregates,
one private selection and one explicitly shared answer. It is capped at 16 KiB.
Presenter rosters are paginated, 25 summaries at a time. Existing message/view,
worker security, evaluation and queue limits remain in place.

The generic host owns authentication, record scope/limits, stable roster numbers,
atomic writes with jobs/receipts, reset and pagination. Query-plan owns answer
validation, cost facts, grading, phases, selected/shared snapshots and aggregate
counts. Neither host routes nor database tables know Query-plan domain rules.

Acceptance checks:

- 600 distinct accepted answers, existing-actor replacements and correct latest
  feedback; direct storage-bound tests at 1000 actors and rejection beyond it.
- Bounded shared state, per-record values, hook input and all audience views.
- Participant identity isolation, private solutions, paginated inspection and
  explicit anonymous sharing.
- Atomic queue/storage failures, replay, concurrent CAS, restart, reset and late
  evaluation delivery across epochs.
- Real presenter evaluator under production CSP; bursts, repeated submissions,
  absent/disconnected/silent evaluator recovery. Report latency and traffic.
- All three browser flows, real LaTeX authoring, installed-wheel/sdist checks and
  regressions for existing providers.

Local targets are p95 submission acknowledgement within five seconds and all
600 initial evaluations within sixty seconds on the recorded test machine.
Failures must be reported and investigated, not hidden by relaxing deadlines or
security. Synthetic loopback results do not establish physical-phone, Wi-Fi or
Internet capacity. Classroom-network and screen-reader checks remain manual gates.

Implementation and local evidence are recorded in [validation](query-plan-600-validation.md).
The initial 600-student timing targets passed; repeated replacement bursts remain
slower (acknowledgment p95 about 11–19 seconds). Physical classroom testing and
publication gates remain open. Existing courses,
environments, provider pins and the original repository remain unchanged.
