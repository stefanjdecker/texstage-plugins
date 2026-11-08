# Teaching notes and reference outcomes

All tasks use the declared model in data/README.md. A name is not a key merely
because the four displayed names happen to differ. Book rows identify physical
copies, and historical loans can refer to a copy more than once.

## SQL

| Example | Expected rows | Useful misconception |
| --- | --- | --- |
| [Filter](answers/sql-filter.sql) | Database Basics; Practical SQL | Returning every title ignores the predicate |
| [Join](answers/sql-join.sql) | Ada / Database Basics; Ben / Graph Stories; Cara / Network Notes | Equality to NULL is not IS NULL |
| [Count](answers/sql-count.sql) | Ada 1; Ben 1; Cara 1; Dan 0 | COUNT(*) counts the NULL-extended row |
| [Available books](answers/sql-available.sql) | Practical SQL | A closed historical loan does not exclude a simultaneous open loan from consideration |
| [Bags](answers/sql-bags.sql) | Ada; Ada; Ben; Ben; Cara | DISTINCT changes the requested multiplicity |

The query checker ignores row order and output-column labels, but respects column
order, values and duplicate multiplicity. The reference queries are examples of
valid solutions; learners can use other SQL formulations.

For the count task, ask learners to predict what happens after adding a member
with only returned loans. A filter in WHERE may drop this member entirely.
Putting the open-loan condition in the join predicate preserves them. Then add
another member named Ada: grouping only by name incorrectly combines different
members. The executable checker includes both cases.

SQL submissions are read-only. The seed creates tables once when the activity
loads; a student's DROP/INSERT/UPDATE is refused and does not alter later work.

## RDF, SPARQL and Turtle

| Example | Expected result |
| --- | --- |
| [SELECT](answers/sparql-select.rq) | The same three name/title pairs as the SQL join |
| [ASK](answers/sparql-ask.rq) | false: no open-loan pattern for Dan in this supplied graph |
| [CONSTRUCT](answers/sparql-construct.rq) | ada borrows b101; ben borrows b102; cara borrows b104 |
| [One Turtle fact](answers/turtle-one.ttl) | ben borrows b102 |
| [Turtle shorthand](answers/turtle-many.ttl) | ada hasBorrowed b101; ada hasBorrowed b103 |

Identifiers in this table are abbreviated with the seed's default prefix.
SPARQL SELECT returns RDF bindings, ASK a boolean, and CONSTRUCT a graph. The
constructed graph is an output; it does not modify the seed.

ASK false describes pattern matching in the supplied graph. It does not establish
that a fact is false in every larger graph or in the real world. The explicit
open/closed status in this seed avoids treating a missing return-date assertion
as evidence that a loan is open.

Turtle is data syntax. A resource such as :b102 differs from the string
"Graph Stories". Full IRIs and prefixed names can identify the same resource.
Comma shorthand and separate statements can express the same graph. Repeating
an identical triple does not duplicate a graph fact. These examples avoid blank
nodes and do not claim support for general graph-isomorphism reasoning.

## Discussion activities and quizzes

- **ER sketch:** require Member, Book and Loan with identifiers. Each Loan refers
  to exactly one Member and one Book; each parent participates in zero to many
  historical loans. Accept different explained notations. Discuss the drawing
  in the gallery; do not call the sketch interface an ER correctness checker.
- **Reviewed graph:** approve the three active borrowing facts. It is a graph of
  contributed labels, not a Turtle parser or an update to the RDF seed.
- **Classification graph:** Database Basics and Practical SQL point to databases;
  Graph Stories to graphs; Network Notes to networks. Two distinct participants
  must support an edge when Minimum is two.
- **Key/constraint questions:** member_id is the key; loans reference existing
  members. Dan demonstrates optional borrowing. Names are not unique.
- **True/false, numeric and text:** false; three; DISTINCT.
- **Ordering:** FROM/JOIN, WHERE, GROUP BY, HAVING, SELECT, ORDER BY. This is a
  conceptual reasoning order and does not prescribe optimizer execution.
- **Word cloud:** distinguish entity types Member/Book/Loan from Ada or title.
- **Explanation list:** a retained join row is not a real loan; COUNT(*) counts
  it, while COUNT(loan_id) ignores its NULL. Ask for a repair.
- **Poll:** no correct answer. The instructor decides how to act on preferences.

## Plugin sections

The copied exercise sources are the established synthetic examples from the
focused decks. Each section declares its own schema, tree, schedule or statistics;
they do not inherit or mutate the SQL/RDF seeds. The prepared sources are under
this master directory so the host's source confinement remains intact.

### Er Decisions

- **er_registrations:** Select cardinalities, status ownership and relationship/entity representation. Both intended alternatives can pass.

### Relational

- **ra_construct:** Construct a join/filter/projection tree. Inspect intermediate tables; matching finite instances is not an equivalence proof.
- **ra_rewrite:** Push filters down using checked rules. Explain each side condition; fewer intermediate cells are a teaching metric.

### Query Plan

- **plan_selective:** Compare the supplied cost formulas: 5,210 teaching units for the index versus 20,000 for a scan.
- **plan_broad:** A broad predicate can make an index worse. Keep the query fixed and compare the root cost.
- **plan_library:** Choose access paths, join order and methods for a library query. Duplicate loan results are meaningful.
- **plan_memory:** Choose the hash build side and obey each operator's memory bound. A previously attractive plan may become illegal.

### Bplus

- **bplus_lookup:** Follow separators to the correct leaf and identify the entry. Leaves store data; internal keys route the search.
- **bplus_range:** Start at the lower-bound leaf, then follow leaf links. Include exactly the required keys and pages.
- **bplus_insert:** Preserve sorted entries, leaf links and separator meaning. Different legal repairs are accepted.
- **bplus_delete:** Inspect occupancy. Borrow or merge as needed, and update the parent separators.
- **bplus_cascade:** Carry a split into an internal page and possibly a new root; preserve existing page identities.
- **bplus_shrink:** A root with one child is removed. The new root must still describe the complete leaf order.

### Functional Dependencies

- **fd_closure:** Apply an FD only when every left-hand attribute is known. Continue to a fixed point.
- **fd_practice:** This activity gives practice feedback and no points. Use it before the scored reasoning examples.
- **fd_keys_one:** A key must determine every attribute and be minimal by inclusion.
- **fd_keys_all:** Completeness matters as well as validity: an omitted key makes an all-keys answer incomplete.
- **fd_implied:** Give a productive derivation. A claim of implication without its required evidence is incomplete.
- **fd_refuted:** Construct two rows satisfying every given FD while agreeing on the proposed determinant and disagreeing on its dependent.
- **fd_different_sizes:** Minimal does not mean minimum cardinality. Candidate keys of different sizes may coexist.
- **fd_empty_key:** An empty determinant can determine all attributes under the stated FDs; do not silently assume keys must be nonempty.

### Normalization

- **norm_registration:** Keep the student/course link. Attribute coverage and dependency preservation alone do not prove losslessness.
- **norm_classify:** Find the highest normal form and a violating dependency for the next one. Assume atomic values.
- **norm_tradeoff:** A lossless BCNF decomposition can fail to preserve an FD. Examine the chase and counterexample rather than only the label.

### Transactions

- **tx_counter:** Predict 110, inspect remembered reads, explain the cycle, then repair to a legal acyclic schedule. The serial result is 120.
- **tx_independent:** Operations on different objects do not create conflicts. Include isolated transactions in a serial certificate.
- **tx_read_read:** Reading the same object twice does not create a conflict. Avoid adding an edge just because the object is shared.
- **tx_write_write:** Write/write pairs can conflict. Explain the earlier/later operation witness for each directed edge.
- **tx_chain:** Distinguish direct conflict edges from reachability. A transitive path is not an extra direct witness.
- **tx_blind_write:** Conflict serializability is sufficient, not necessary for view serializability. A matching final value does not prove the conflict graph acyclic.

## Facilitation and scoring

For prepared lessons, first explain the printed data, then open the answer phase.
Let students think and save explicitly. Wait for evaluation, inspect privately,
close participation where required, share anonymously, and reveal the evidence.
A changed draft or local preview is not a submitted answer. Pending or unavailable
evaluation is not an incorrect answer.

Transactions use their own sequence: Predict, Inspect execution, Diagnose,
Repair, Reveal. Reaching the final trace step (or advancing to Diagnose) releases
prediction feedback; full diagnosis/repair feedback follows at Reveal.
For query-plan examples, explain the 120-second timed scoring rule before opening.

| Examples | Points / feedback |
| --- | --- |
| Original quizzes and code/graph activities | No quiz points; reference or discussion feedback |
| Coordinate, ER, relational, transactions | Formative feedback, no scoreboard points |
| Six B+ activities | Up to 1,000 fixed points each, component partial credit |
| FD practice | Zero points, practice feedback |
| Seven other FD activities | 100 fixed points each under their checked rubric |
| Three normalization activities | 1,000 fixed points each |
| Four query-plan activities | 1,000 base quiz points, 120-second rounds; speed and shared streak rules apply |

The latest checked answer controls an activity's award; saving repeatedly does
not accumulate fixed points. Reveal publishes configured awards; reset withdraws
them. Plugin points are independent of the deck's built-in quiz points setting.
See the individual lesson guides for each rubric and any reopen restrictions.
This mixed reference deck is not intended as a balanced graded examination.

For practice-only demonstrations, use a copy of the sources and follow each
provider's documented points/feedback options, then rebuild and use a fresh
session. Do not change the original course environments.

## Short route and topic sessions

For an instructor-led tour, use logical slides 1–6 (orientation and coordinate input),
14 (sql-join), 24 (ra_construct), 27 (plan_selective), 32 (bplus_lookup), 41 (fd_keys_one), 49 (norm_classify), 54 (sparql-select), 60 (tx_counter), and 70 (takeaways).
Use COVERAGE.md and the overview to locate the named activities; allocate a few
minutes per selected task if students participate rather than just watch.
A participatory tour covering every family needs more than this short route.

For a topic session, run the relevant introduction and all activities in that
section. The complete 70-slide reference collection is several lessons, not
a promised one-hour lecture. Rehearse the printed examples and real phone/network
flow before class; the repository's classroom-device checklist remains applicable.
