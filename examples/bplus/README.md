# B+ tree prepared examples

The [author guide](../../docs/bplus-lesson.md) explains installation, explicit
enablement, source fields and every output command.

- `lesson.tex` / `lesson.en.activities.json`: English 16:9 teaching progression.
- `lesson-de.tex` / `lesson.de.activities.json`: German, using the same six sources.
- `layout-stress.tex` / `layout-stress.en.activities.json`: empty, last-entry and
  40-entry cases on a taller 160 × 120 mm 4:3 page.
- `layout-stress-de.tex` / `layout-stress.de.activities.json`: German stress cases.

The sources in `activities/` are synthetic public examples. Each slide starts
from its own tree. Edit the JSON once; preparation derives the live exercise,
diagram and checked solution. Change the worked certificate with the exercise,
or the build will stop.

Version 0.7.0 provides structured phone answers, local preview, private presenter
inspection, anonymous sharing and replay. Follow the
[classroom guide](../../docs/bplus-classroom.md) to run the examples.
The six teaching sources each set **points: 1000**; the stress sources default
to practice. The [rubric](../../docs/bplus-scoring.md) appears on phones and
exercise sheets; reveal publishes points to TeXStage's scoreboard.
The source files include worked answers for
authors; distribute the generated exercise PDF/PPT to students, not raw author
sources or preparation directories containing solutions.
