# Transaction examples

Start with [the lesson guide](../../docs/transactions-lesson.md). The English and
German decks each have an introduction and six activities: lost update,
independent objects, read/read, write/write, a three-transaction chain, and a
blind-write counterexample. Every lesson has independently checked alternative
repairs. `layout-stress*.tex` tests three objects, long IDs and fifteen operations.

Build and serve in an isolated profile with both transaction providers enabled:

```sh
texstage present examples/transactions/lesson.tex --activities examples/transactions/lesson.en.activities.json --data ./transaction-profile --plugins-lock ./transactions.lock.json --no-tunnel
```

`lesson.activities.json` is the English alias. Choose matching German files for
German output. Run `maintenance/transaction_authoring_probe.py --output NEW_DIR`
to build, inspect and render both languages and both stress fixtures without
editing these sources. The activity is formative and awards no points.
