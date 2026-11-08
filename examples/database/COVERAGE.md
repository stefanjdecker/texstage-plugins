# Activity coverage

Both editions have identical activity IDs and coverage. Links below point to
English files in `slides/`; German counterparts have the same filenames under
[slides-de/](slides-de/). Both masters share [database-sequence.tex](database-sequence.tex)
and all prepared exercise sources.

The deck has 70 logical slides and 53 interactive examples: ten quizzes covering
all nine quiz types, twelve built-in activities, and 31 plugin activities.
Thirty plugin examples use prepared JSON sources; the coordinate example uses
its original inline LaTeX contract. These cover all eight current content types
and the main teaching modes; stress-test fixtures are kept in the focused decks.
This is a reference collection, not a complete database curriculum.

## Built-in activities

| Activity ID | Interaction | Source | What students do |
| --- | --- | --- | --- |
| primary-key | Single choice | [04](slides/04-primary-key.tex) | Use a declared primary-key constraint |
| constraints | Multiple choice | [05](slides/05-constraints.tex) | Distinguish keys, references and optional borrowing |
| er-sketch | Sketch | [06](slides/06-er-sketch.tex) | Model Loan as an entity with cardinalities |
| sql-filter | SQL | [08](slides/08-sql-filter.tex) | Select book titles by topic |
| sql-join | SQL | [09](slides/09-sql-join.tex) | Join three tables and test IS NULL |
| sql-count | SQL | [10](slides/10-sql-count.tex) | Preserve members with zero open loans |
| sql-available | SQL | [12](slides/12-sql-available.tex) | Find absence with an anti-join |
| sql-bags | SQL | [13](slides/13-sql-bags.tex) | Preserve duplicate result rows |
| duplicates | True/false | [14](slides/14-duplicates.tex) | Explain the effect of DISTINCT |
| active-total | Numeric slider | [15](slides/15-active-total.tex) | Count open loans |
| distinct-keyword | Text answer | [16](slides/16-distinct.tex) | Name DISTINCT |
| query-order | Ordering | [17](slides/17-query-order.tex) | Separate logical clause order from a physical plan |
| crowd-facts | Three-field graph | [19](slides/19-crowd-facts.tex) | Submit and review labeled borrowing edges |
| crowd-pairs | Two-field graph | [20](slides/20-crowd-pairs.tex) | Classify books with two-person agreement |
| sparql-select | SPARQL SELECT | [21](slides/21-sparql-select.tex) | Join graph patterns into bindings |
| sparql-ask | SPARQL ASK | [22](slides/22-sparql-ask.tex) | Ask about a pattern in the supplied graph |
| sparql-construct | SPARQL CONSTRUCT | [23](slides/23-sparql-construct.tex) | Derive borrowing triples |
| turtle-one | Turtle | [24](slides/24-turtle-one.tex) | Use a resource, not its title literal |
| turtle-many | Turtle | [25](slides/25-turtle-many.tex) | Express two triples using shorthand |
| entity-cloud | Open word cloud | [26](slides/26-word-cloud.tex) | Distinguish types, instances and attributes |
| explain-zero | Open response list | [27](slides/27-explain.tex) | Explain a NULL-extended join row |
| topic-poll | Multiple-selection poll | [28](slides/28-topic-poll.tex) | Choose a topic to revisit |


## Plugin activities

| ID | Exercise | Slide source | Prepared source |
| --- | --- | --- | --- |
| shelf-point | Coordinate choice and distance feedback | [warm-up](slides/32-coordinate-warmup.tex) | Inline LaTeX |
| er_registrations | Choose a model for workshop registrations | [11](slides/34-er-registrations.tex) | [JSON](activities/er-decisions/registrations.json) |
| ra_construct | Build a query tree | [24](slides/36-ra-construct.tex) | [JSON](activities/relational/construct.json) |
| ra_rewrite | Rewrite a query tree | [25](slides/37-ra-rewrite.tex) | [JSON](activities/relational/rewrite.json) |
| plan_selective | Few matches: scan or index? | [27](slides/39-plan-selective.tex) | [JSON](activities/query-plan/selective.json) |
| plan_broad | Many matches: scan or index? | [28](slides/40-plan-broad.tex) | [JSON](activities/query-plan/broad.json) |
| plan_library | Choose a join order | [29](slides/41-plan-library.tex) | [JSON](activities/query-plan/library.json) |
| plan_memory | Plan with less hash memory | [30](slides/42-plan-memory.tex) | [JSON](activities/query-plan/memory.json) |
| bplus_lookup | Follow a lookup path | [32](slides/44-bplus-lookup.tex) | [JSON](activities/bplus/lookup.json) |
| bplus_range | Scan a key interval | [33](slides/45-bplus-range.tex) | [JSON](activities/bplus/range.json) |
| bplus_insert | Insert and split a leaf | [34](slides/46-bplus-insert.tex) | [JSON](activities/bplus/insert.json) |
| bplus_delete | Delete and repair underflow | [35](slides/47-bplus-delete.tex) | [JSON](activities/bplus/delete.json) |
| bplus_cascade | Propagate a split | [36](slides/48-bplus-cascade.tex) | [JSON](activities/bplus/cascade.json) |
| bplus_shrink | Shrink the root | [37](slides/49-bplus-shrink.tex) | [JSON](activities/bplus/shrink.json) |
| fd_closure | Derive an attribute closure | [39](slides/51-fd-closure.tex) | [JSON](activities/functional-dependencies/closure.json) |
| fd_practice | Practice a closure with feedback | [40](slides/52-fd-practice.tex) | [JSON](activities/functional-dependencies/practice.json) |
| fd_keys_one | Find one candidate key | [41](slides/53-fd-keys-one.tex) | [JSON](activities/functional-dependencies/keys_one.json) |
| fd_keys_all | Find all candidate keys | [42](slides/54-fd-keys-all.tex) | [JSON](activities/functional-dependencies/keys_all.json) |
| fd_implied | Prove an implied dependency | [43](slides/55-fd-implied.tex) | [JSON](activities/functional-dependencies/implied.json) |
| fd_refuted | Refute a dependency | [44](slides/56-fd-refuted.tex) | [JSON](activities/functional-dependencies/refuted.json) |
| fd_different_sizes | Compare candidate-key sizes | [45](slides/57-fd-different-sizes.tex) | [JSON](activities/functional-dependencies/different_sizes.json) |
| fd_empty_key | Can an empty key work? | [46](slides/58-fd-empty-key.tex) | [JSON](activities/functional-dependencies/empty_key.json) |
| norm_registration | Decompose while keeping registrations | [48](slides/60-norm-registration.tex) | [JSON](activities/normalization/registration.json) |
| norm_classify | Classify a relation | [49](slides/61-norm-classify.tex) | [JSON](activities/normalization/classify.json) |
| norm_tradeoff | Compare losslessness and FD preservation | [50](slides/62-norm-tradeoff.tex) | [JSON](activities/normalization/tradeoff.json) |
| tx_counter | Two increments, one counter | [60](slides/63-tx-counter.tex) | [JSON](activities/transactions/counter.lesson.json) |
| tx_independent | Independent transactions | [61](slides/64-tx-independent.tex) | [JSON](activities/transactions/independent.lesson.json) |
| tx_read_read | Shared reads | [62](slides/65-tx-read-read.tex) | [JSON](activities/transactions/read_read.lesson.json) |
| tx_write_write | Competing writes | [63](slides/66-tx-write-write.tex) | [JSON](activities/transactions/write_write.lesson.json) |
| tx_chain | Direct edges and a chain | [64](slides/67-tx-chain.tex) | [JSON](activities/transactions/chain.lesson.json) |
| tx_blind_write | A blind-write limitation | [65](slides/68-tx-blind-write.tex) | [JSON](activities/transactions/blind_write.lesson.json) |

Each transaction example includes prediction, trace inspection, diagnosis and
repair within one activity. The two relational modes are construction and checked
rewriting. B+ covers all four operations plus cascading split and root shrink.
FD covers closure, one/all keys, proved/refuted implication and boundary cases.
Normalization includes classification and decomposition; query planning includes
selectivity, join order and memory constraints. ER checks constrained choices;
the earlier freehand sketch remains a human discussion task.

Additional empty/large-tree and maximum-schedule stress fixtures live in
[the B+ examples](../bplus/README.md) and [transaction examples](../transactions/README.md).
No standalone slide is needed for the distance or transaction engine package:
the coordinate and transaction activities exercise those dependencies.
