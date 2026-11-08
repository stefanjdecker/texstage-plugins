# English and German

All eight classroom content types have English and German interfaces:
coordinates, ER decisions, relational algebra, query plans, B+ trees, functional
dependencies, normalization and transaction schedules. The separate distance and
transaction engines have no classroom interface. Technical identifiers, SQL/RDF
syntax and some diagnostic codes are not translated.

## Select the language

Keep these two author settings consistent:

| Setting | English | German | Controls |
| --- | --- | --- | --- |
| Main LaTeX language | `\usepackage[english]{babel}` | `\usepackage[ngerman]{babel}` | Live plugin controls on presenter, projector and phone |
| Activity sidecar | `"language": "en"` | `"language": "de"` | Prepared exercise and solution text |

The sidecar setting is top-level, next to `format` and `items`. Pass that file
explicitly as `--activities`. With multiple Babel languages, select the main
language explicitly, for example `\usepackage[main=ngerman,english]{babel}`.
Rebuild after changing either setting. Changing a phone's language does not
translate an already built deck.

The deck language is derived from Babel/Polyglossia and stored in `deck.json`.
TeXStage passes it to each plugin as `ctx.language`; missing or unsupported deck
languages fall back to English. It applies to the whole deck. There is no
per-student plugin language selector.

The phone's join screen, waiting messages, quiz controls, Q&A and built-in
activity controls follow the presentation language too. Scanning the QR code
or entering a valid PIN selects it before joining, even when the browser uses
another language. Reconnecting keeps the session's language. The browser
language is only the fallback while no session is identified; decks without a
supported language use English. The main presenter toolbar remains separate
from provider-owned controls; this guide does not claim every host interface
or technical engine diagnostic is translated.

## Supply translated content

Selecting German does not translate authored text. Write German frame titles,
quiz questions, choices, notes and activity prompts. Prepared lessons use the
provider's German text fields, usually `{"en": "...", "de": "..."}`. Refer to
each authoring guide: field shapes and missing-translation behavior differ.
Some providers fall back to English; do not rely on fallback for a fully German
lesson. Keep schema identifiers, formulas and reference answers stable unless
you deliberately change the exercise.

The built-in LaTeX quiz/activity styles also have author-configurable static
labels. Set `\quizsetup{handout-heading={Live-Quiz},true-label={Wahr},...}` and
redefine `\texactivitylabel` and `\texactivityreferencelabel` as needed. The
[German master](../examples/database/database-de.tex) shows the complete setup,
including handout placeholders and answer hints, without requiring a DBIS theme.

Coordinates uses inline LaTeX, so it needs no sidecar of its own. Its controls,
feedback, decimal formatting and accessible grid labels follow the deck.
Distance does not determine correctness: `(0,5)` and `(3,4)` still have the same
distance but are different answers.

## Complete example

The [database lab](../examples/database/README.md#language) provides matching
English and German masters and sidecars, with 70 slides and 53 interactive
examples in each. Both use the same data, answers, layout and slide order.
Its [validation record](../examples/database/VALIDATION.md) distinguishes build
and browser coverage from testing real phones on a classroom network.
