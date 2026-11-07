# Using the ER lesson with a keyboard or assistive technology

Version 0.4.1 adds field-specific validation and focus recovery to the
registration pilot. The activity uses the deck's English or German language;
the phone's general TeXStage controls may use the browser language instead.
The [lesson guide](er-decisions-lesson.md) explains the modelling decisions.

## Keyboard workflow

1. Join the lecture, then use Tab or Shift+Tab to move between decision cards,
   the optional reason and action buttons. In a card, use the arrow keys to
   change the selected radio option; Space selects the focused option.
2. Choose **View model**. Focus moves to the preview heading. The schematic is
   repeated in the named **Constraints in words** list, including participation
   bounds, the owner of status and pair uniqueness. **Back to decisions**
   returns focus to the preview button without changing your choices.
3. When the teacher opens answers, choose **Save answer**. An incomplete
   answer focuses the first missing decision. An invalid reason returns to
   the editor and focuses the reason field, including when saving from the
   model preview. The affected controls expose the error as their description.
4. A saved answer is evaluated on the presenter's computer. Phase changes and
   your answer's status have separate polite status regions. Unchanged state
   messages are not rewritten on every classroom update. Correctness feedback
   remains private until the teacher reveals it.
5. If another device saves your answer or the teacher resets the activity,
   an alert explains the conflict. **Keep my draft** and **Reload saved answer**
   are explicit choices; neither saves an answer. Focus returns to the first
   decision when editing, or the visible heading when previewing.

The presenter can operate phase, paging, selection and sharing controls with
the keyboard. Counts remain available for reading without announcing every
student response. The anonymous projector view has a textual model alternative;
private inspection and reasons are not projected without explicit sharing.

## Automated evidence

The [validation record](design/er-accessibility-validation.md) identifies the
installed wheels and the results for Chromium, Firefox and WebKit in both
languages. Tests cover real keyboard navigation, field errors, focus recovery,
phase/feedback semantics, named regions and model alternatives, independent
radio groups in multiple mounts, and repeated-update behaviour. They save
accessibility-tree snapshots and screenshots. They also check narrow-phone
layout and doubled text size.

The [native-zoom follow-up](design/er-native-zoom-validation.md) adds real
200% Chrome page zoom in English and German. It verifies the changed pixel
ratio and viewport, keyboard access to private inspection and sharing controls,
scrolling through projected alternatives, and separate presenter panes and
toolbar. Screenshots capture the browser's actual compositor. This uses a
zoomed desktop participant view; it does not replace the 320-pixel phone check.

Accessibility-tree and live-region DOM tests do **not** verify what a screen
reader actually speaks. Text-size emulation does not prove native browser
zoom behaviour. Physical devices and screen-reader review remain open gates.

To reproduce, install the matching host/provider wheels and locked test
dependencies in an isolated environment, then install Playwright's browsers:

```console
python maintenance/er_ui_bundle.py --output artifacts/er-accessibility-en
python maintenance/er_ui_bundle.py --output artifacts/er-accessibility-de --language de
node maintenance/er_accessibility_browser.cjs artifacts/er-accessibility-en/out/lesson.bundle artifacts/er-accessibility
node maintenance/er_accessibility_browser.cjs artifacts/er-accessibility-de/out/lesson-de.bundle artifacts/er-accessibility
```

Set `PYTHON` to that environment's interpreter and `BROWSER` to `chromium`,
`firefox` or `webkit`. Use a different `TEXSTAGE_TEST_PORT` for simultaneous
runs. The helper builds disposable copies of the example, leaving courses
unchanged. The [ER CI workflow](../.github/workflows/er-conformance.yml) runs
these checks on the same wheel/bundle handoff as the other browser gates.

For native Chrome zoom, also install Chrome (`npx playwright install chrome`).
Set `BROWSER=chromium` and `ER_NATIVE_ZOOM=2`, then run the same two accessibility
commands. In PowerShell, use `$env:BROWSER='chromium'` and
`$env:ER_NATIVE_ZOOM='2'`. The helper creates disposable browser profiles,
checks Chrome's native zoom setting, and writes results under
`en/chromium-zoom2` and `de/chromium-zoom2`. Clear `ER_NATIVE_ZOOM` before running
the ordinary three-browser/320-pixel checks. The CI workflow has a separate
native-zoom job; its hosted run is still pending.

## Manual review still required

Record the provider payload, host artifact, device model, OS, browser, screen
reader/version, input method and network before each review. Keep observations
with the release evidence; an unchecked row is not a pass.

| Review | Expected result | Status |
| --- | --- | --- |
| Physical Android and iPhone: join, choose, preview, save, repair and reconnect | All controls reachable and content readable | Not performed |
| Screen reader: read each card and its options | Group names and option explanations are understandable | Not performed |
| Screen reader: save incomplete choices and an overlong reason | Error is announced with its field; focus is visible and useful | Not performed |
| Screen reader: close/reopen/reveal and unrelated responses | Relevant status is announced without repeated classroom chatter | Not performed |
| Screen reader: reset while editing and previewing | Conflict choices are discoverable; focus stays in the activity | Not performed |
| Screen reader: read the model and checked alternatives | All visual constraints have an understandable text equivalent | Not performed |
| Native Firefox/Safari zoom and OS text enlargement | Controls and explanations remain usable without lost content | Not performed |

Do not record student names, submissions or reasons in public validation
reports. Use the supplied synthetic registration activity for these checks.

## Version 0.5.0 capacity follow-up

The [600-student validation](design/er-600-validation.md) identifies the current
host/provider and browser checks. Phones no longer show a changing whole-class
count; their own phase and answer announcements remain. Historical 0.4.1 reports
retain their original artifact identities and do not certify new artifacts.
