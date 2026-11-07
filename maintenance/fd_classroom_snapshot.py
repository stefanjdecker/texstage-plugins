# SPDX-License-Identifier: Apache-2.0
"""Inspect only an owned synthetic load-test database, without changing it."""
import json
from pathlib import Path
import sqlite3
import sys

from texstage.plugins.manifest import canonical

db = sqlite3.connect(Path(sys.argv[1]).as_uri() + '?mode=ro', uri=True)
row = db.execute('SELECT sid,kind,epoch,state FROM items WHERE item=?', (sys.argv[2],)).fetchone()
shared = json.loads(row[3])
if 'answers' in shared:  # Retain the harness for historical 0.3.0 comparisons.
    actors = shared['answers']
else:
    actors = {a: json.loads(s) for a, s in db.execute(
        'SELECT actor,state FROM actor_states WHERE sid=? AND kind=? AND item=? AND epoch=?',
        (row[0], row[1], sys.argv[2], row[2]))}
sizes = [len(canonical({a: s})) for a, s in actors.items()]
print(json.dumps({'state_bytes': len(row[3].encode()), 'max_actor_slot_bytes': max(sizes, default=0),
                  'total_actor_bytes': sum(sizes), 'actors': len(actors),
                  'pending_jobs': db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','leased')").fetchone()[0]}))
db.close()
