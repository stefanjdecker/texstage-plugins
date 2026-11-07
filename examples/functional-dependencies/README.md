# Functional dependencies, keys and implication

Build `lesson.tex` with `lesson.activities.json` using the matching FD Lab 0.6.0
and TeXStage integration wheels. See the [installation and teaching guide](../../docs/fd-lesson.md).
Existing course installations do not need to change.

The eight activities use workshop registrations, rooms and buildings. Students
construct closures, find one or all candidate keys, and prove or refute an FD.
They also encounter keys of different sizes and the empty key.

Each activity JSON has a top-level `points` field. Seven exercises award 100
points for a verified correct answer; `practice.json` awards none. Immediate
mathematical feedback in a practice-feedback exercise does not publish its points.
Use **Reveal solution** to publish the latest verified awards. Pending work can
finish afterward. Incorrect answers receive zero; unavailable evaluations remain
ungraded. A retry or replacement does not accumulate extra points.

The phone shows the learner's award; the normal game total, ranking and results
CSV include it. Scored rounds require **Reset activity** before reopening after
reveal. Reset removes their previous awards. Set `points` to zero, or omit it,
for an unscored lesson. Rebuild the bundle after changing the source.
