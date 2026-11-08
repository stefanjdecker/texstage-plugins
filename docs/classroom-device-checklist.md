# Phone and classroom acceptance checklist

Status: **not performed**. Prepared on 2026-11-08 for a later rehearsal on the
intended classroom network. Automated browser and synthetic load tests do not
replace this check. Use synthetic names and answers; keep recordings, private
archives, presenter keys and student data out of the public repository.

Allow about 30 minutes for transactions and another 20 minutes for the relational
editor. Record each device/browser separately. An unchecked item is not a pass.

## Record the setup

| Field | Record before testing |
| --- | --- |
| Date, tester, room and network | |
| Host commit and wheel SHA-256 | |
| Collection commit and plugin wheel SHA-256/payload | |
| Deck, language and bundle identity | |
| Server OS, Python version, CPU/RAM | |
| Presenter browser/version and laptop power mode | |
| Phone model, OS, browser/version | |
| Screen reader/version and input method | |
| Server URL, network path and concurrent clients | No credentials |

Use a disposable environment and operator profile following the
[transaction guide](transactions-lesson.md) and
[relational guide](relational-lesson.md). Install the tested artifacts, explicitly
enable their payloads, and start a fresh session with the supplied English or
German example and matching sidecar. Keep existing course pins and production
sessions unchanged.

Have Android/Chrome and iPhone/Safari phones, the presenter laptop and a separate
projector window available. Use the intended deployment URL: a phone's
`localhost` is the phone itself. Verify ordinary HTTPS/certificate and network
configuration; do not disable browser security or the plugin sandbox. Keep the
presenter tab open and awake while it evaluates submissions.

## Join and read

- [ ] Scan the QR code on classroom Wi-Fi; join each phone with a distinct
  synthetic name. No presenter key is needed on a participant phone.
- [ ] Read in portrait/landscape and at 200% text zoom. Prompts, labels, errors,
  feedback and Save remain usable. Wide tables can scroll and the software
  keyboard does not hide the current field.
- [ ] Repeat core actions in German. Long labels fit and messages use the
  selected language.
- [ ] Check the other phone and projector: neither exposes another student's
  private answer, roster, identity, reference solution or early feedback.

## Transaction lesson

Use the counter example first, then the chain example with multiple conflicts.

- [ ] **Predict:** enter/change a value slowly and choose Save answer. Typing alone
  does not submit. The saved state is clear; correctness remains hidden.
- [ ] Leave an unfinished edit on phone A while phone B saves. A's draft, focus
  and selection survive. Saving A replaces only A's answer.
- [ ] **Inspect execution:** step forward/backward and jump to the final step.
  Phones/projector follow. The end releases prediction feedback; moving backward
  does not pretend to hide it again.
- [ ] **Diagnose:** choose direct edges, witnessing operation pairs and a cycle
  or full serial order. Errors explain what needs attention. Save wrong and
  correct answers; private feedback waits for its release phase.
- [ ] **Repair:** use Move up/down, Insert before and Undo. Preserve transaction
  program order. Save two different valid repairs and verify both pass evaluation.
- [ ] Inspect an answer in the presenter roster: it stays private. Reveal, share
  anonymously, then clear sharing. The projector shows the intended snapshot
  without a student identity.
- [ ] Reset. Old answers/feedback disappear and cannot be restored by a late
  response. Transaction version 1 awards no scoreboard points.

## Relational editor

- [ ] Build a table/filter/projection query with labelled controls. Apply edits,
  select nodes and inspect Result at this node. Preview uses public example data
  and does not claim to prove the answer correct.
- [ ] Try an invalid column/type combination. Read the explanation and repair
  the draft. Switching nodes or saving cannot silently discard unapplied edits.
- [ ] Add a binary operator, edit each input, swap, undo and redo. A peer's save
  preserves the draft, focus and selected node.
- [ ] Apply a legal rewrite rule and try one with unmet preconditions. Check the
  explanation/history; save and follow close/reveal. Inspect shared work and reset.
- [ ] Respect the documented 64-participant pilot limit. Transaction and B+ tree
  measurements do not establish relational-editor capacity.

## Recovery and accessibility

- [ ] Save, briefly disconnect Wi-Fi, reconnect and resume in the same browser.
  The latest saved answer returns once. Repeat while editing and record unsaved
  draft loss separately from saved-data loss.
- [ ] Open the same participant session in a second tab; save conflicting edits.
  A clear keep/reload choice prevents silent overwrite.
- [ ] Lock/unlock a phone and background/restore its browser. Resume without
  cross-student state, stale feedback or unexplained disabled controls.
- [ ] With repairs pending, close the presenter evaluator and reopen through
  the normal authenticated entry. Pending work recovers; unavailable evaluation
  must never be reported as an incorrect answer.
- [ ] Complete the lesson with keyboard only on the laptop: visible focus,
  sensible order, all actions reachable and no keyboard traps.
- [ ] With iPhone VoiceOver and Android TalkBack, read prompts, labels, selected
  states, errors and save/evaluation feedback. Complete a prediction, conflict
  selection, card move and tree edit without relying on colour. Dynamic updates
  must not repeatedly steal focus or announce the whole page.
- [ ] If recording is used, make a short private screen/window recording and
  play it back. Confirm readable slides, intelligible audio and the intended
  capture surface. Keep this test recording private.

## Timing and acceptance

Record save-to-acknowledgement, save-to-checked-feedback, presenter-control delay,
disconnects and recovery separately. Try human-paced actions and a simultaneous
save by available devices. Record the actual phone count: two phones establish
neither 600 nor 1,000-device Wi-Fi capacity. Keep synthetic load and physical
network evidence distinct.

| Device/browser | Scenario | Pass/fail/not tested | Timing or problem |
| --- | --- | --- | --- |
| | | | |

Acceptance requires no lost saved answer, cross-student disclosure, early private
feedback, silent overwrite, inaccessible required action or failed recovery.
Record reproducible issues with sanitized steps, exact artifact identities and
device details. Resolve failures and fill in the relevant rows before marking
the physical-device/classroom gate complete.
