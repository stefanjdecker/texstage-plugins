# Worked Query-plan Challenge design examples

These fixtures are accepted by the installed cost engine's
[frozen v1 contract](../query-plan-challenge-contract.md). They are not yet
classroom activities. [exercises.json](exercises.json) maps fixture names to
engine sources; [expected-cases.json](expected-cases.json) contains hand-derived
plan expectations. The authoritative schemas are in the
[provider package](../../../plugins/query-plan/texstage_query_plan/schemas).
The adjacent original draft schemas remain historical design artifacts.

See the [design](../query-plan-challenge.md) for exact semantics and limitations
and the [implementation plan](../query-plan-challenge-plan.md) for remaining work.

Run from the collection root:

```sh
python maintenance/check_query_plan_design.py
```

The checker uses only the Python standard library. It checks these trusted small
fixtures, compares independent expected values, exhaustively enumerates their
bounded plan families and prints a deterministic report. To intentionally refresh
the checked-in evidence, add --write-report. It is not a production JSON validator,
plugin engine, schema conformance suite or browser test. The draft schemas are
also validated separately during preparation of this design.

## Scan choice

With index height H=3, N=10,000 rows and P=100 pages:

| Estimated matches | Sequential scan: 100P+N | Index: 400(H+R)+R | Better |
| --- | --- | --- | --- |
| 10 | 20,000 | 5,210 | Index |
| 5,000 | 20,000 | 2,006,200 | Sequential |
| 0 | 20,000 | 1,200 | Index, still pays descent |

These are separate public statistics profiles, not hidden changes after a
submission. In the tie example N=810, P=40, H=2 and R=10, both scans cost 4,810.
Both must satisfy a best-plan goal.

## One row on each side

Two one-row tables occupy one page each; each scan costs 101. Their fixed join
returns one row. A materialized nested join costs 1*1+1=2; either hash join costs
2*1+1+1=4. Totals are 204 and 206. Hash is not always better.

## Library join order

The fixed bag query returns one row per open loan of a database book and
projects the member's name. Different loans may produce duplicate names.

| Relation | Base rows | Pages | Filtered rows | Width | Index |
| --- | --- | --- | --- | --- | --- |
| books | 10,000 | 100 | 10 | 32 | topic, height 3 |
| loans | 50,000 | 500 | 5,000 | 32 | None |
| members | 2,000 | 20 | 2,000 | 32 | None |

Joins: books.book_id = loans.book_id and loans.member_id = members.member_id.
Subset estimates: books+loans = 50; loans+members = 5,000; all three = 50.
books+members is disconnected and has no cardinality record. The public hash
workspace limit is 1,048,576 bytes.

Use an index on books and sequential scans on loans/members: scan costs sum to
5,210 + 100,000 + 4,000 = 109,210.

| Plan decisions | Join costs | Total |
| --- | --- | --- |
| books+loans, hash books; then members, hash first result | (2*10+5,000+50) + (2*50+2,000+50) = 7,220 | **116,430** |
| loans+members, hash members; then books, hash books | (2*2,000+5,000+5,000) + (2*10+5,000+50) = 19,070 | 128,280 |
| books+loans, nested; then members, nested | (10*5,000+50) + (50*2,000+50) = 150,100 | 259,310 |

The better hash order needs 480 bytes at its first hash and 4,000 bytes at the
second. Child-order variants with the same build relation are tied optima; the
checker enumerates them. Hashing all 5,000 filtered loans needs 240,000 bytes.

Now publish a separate exercise with a 1,024-byte workspace limit. Hashing the
10 books still fits; hashing the first 50-row result (width 64) or the 2,000 members
does not. The best plan uses the first small hash and a final nested join:
109,210 + 5,070 + 100,050 = **214,330**.
This is a per-operator hash bound, not total-query memory accounting.

## What the evidence does and does not establish

The checked-in [report](validation.json) identifies fixture/checker hashes,
expected-case results, enumerated candidate counts and minima. Additional design
checks cover child swaps, memory monotonicity, the exact workspace boundary,
missing/duplicate relations, disconnected joins and unavailable indexes.

The exhaustive minimum applies to the declared <=3-relation plan family under
teaching-cost-v1. Statistics are authored estimates; no real rows or database
timings are measured here. The separate [Q0/Q1 record](../query-plan-engine-validation.md) now covers
independent bag-semantics fixtures, adversarial parsing, typed host results,
byte bounds, wheel installation and cross-browser worker security.
Live authoring, UI/role privacy and classroom load remain later gates.
