# SPDX-License-Identifier: Apache-2.0
"""One checked lesson source supplies live data and private/static solutions."""
import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from texstage.plugin_api.v1 import PreparedAuthoring, PreparedItem, latex_escape
from . import layout, model

TYPE = "io.github.stefanjdecker.bpluslab.tree"
ENGINE = "io.github.stefanjdecker.bpluslab.operations"
ROOT = Path(__file__).resolve().parent
LESSON = Draft202012Validator(json.loads((ROOT / "schemas/lesson-v1.json").read_text(encoding="utf-8")))


def localized(value, language):
    return value.get(language, value["en"])


def words(en, de, language):
    return de if language == "de" else en


def _path(pages):
    return " > ".join("P" + str(p) for p in pages)


def _steps(exercise, answer, facts, language):
    """Describe only a certificate that has already passed complete replay."""
    lines = [words("Descent in the starting tree: ", "Abstieg im Ausgangsbaum: ", language) + _path(answer["path"]) + "."]
    if "read" in facts:
        read = facts["read"]
        if exercise["task"]["kind"] == "range":
            lines.append(words("Leaf scan: ", "Blattfolge: ", language) + _path(read["leaves"]) + ".")
        keys = ", ".join(map(str, read["keys"])) or words("(none)", "(keine)", language)
        lines.append(words("Result: ", "Ergebnis: ", language) + keys + ".")
        lines.append(words("Logical page visits: ", "Logische Seitenzugriffe: ", language) + str(read["page_visits"]) + ".")
        return lines
    kinds = {n["id"]: n["kind"] for n in exercise["tree"]["nodes"]}
    next_id, root = max(kinds) + 1, exercise["tree"]["root"]
    for index, repair in enumerate(answer["repairs"], 1):
        page, op = repair["node"], repair["op"]
        leaf = kinds[page] == "leaf"
        if op == "split":
            units = words("entries", "Einträgen", language) if leaf else words("child pointers", "Kindzeigern", language)
            move = words("copy", "kopiere", language) if leaf else words("promote", "verschiebe", language)
            text = (f"Split P{page} after {repair['left_count']} {units}; {move} {repair['separator']} to the parent."
                    if language == "en" else
                    f"Teile P{page} nach {repair['left_count']} {units}; {move} {repair['separator']} in den Elternknoten.")
            kinds[next_id] = kinds[page]
            next_id += 1
            if page == root:
                root = next_id
                kinds[root] = "internal"
                next_id += 1
        elif op == "borrow":
            unit = words("entry", "Eintrag", language) if leaf else words("child pointer", "Kindzeiger", language)
            text = (f"Borrow one {unit} from P{repair['sibling']} into P{page}." if language == "en" else
                    f"Leihe einen {unit} von P{repair['sibling']} an P{page}.")
        else:
            text = (f"Merge P{page} and P{repair['sibling']}; the left page remains." if language == "en" else
                    f"Vereinige P{page} und P{repair['sibling']}; die linke Seite bleibt.")
        lines.append(f"{index}. {text}")
    if not answer["repairs"]:
        lines.append(words("No occupancy repair is needed.", "Keine Belegungsreparatur erforderlich.", language))
    metrics = facts["metrics"]
    lines.append(words("Height (edges): ", "Höhe (Kanten): ", language) +
                 f"{metrics['height_before']} -> {metrics['height_after']}.")
    return lines


def _fragment(public, private, language, solutions):
    exercise, task = public["exercise"], public["exercise"]["task"]
    answer, facts = private["worked"]["answer"], private["worked"]["analysis"]
    shown = facts.get("final", exercise["tree"]) if solutions else exercise["tree"]
    highlighted = facts.get("read", {}).get("path", []) + facts.get("read", {}).get("leaves", []) if solutions else []
    diagram, mode = layout.tikz(shown, highlighted=highlighted, key=task.get("key") if solutions else None)
    e = latex_escape
    heading = words("One checked solution", "Eine geprüfte Lösung", language)
    lines = [r"\begingroup\begin{lrbox}{\bplusbox}\begin{minipage}{\linewidth}\raggedright",
             r"\fontsize{10}{11.5}\selectfont\textbf{" + e(localized(public["title"], language)) + r"}\par",
             r"\fontsize{8.5}{10}\selectfont " + e(localized(public["prompt"], language)) + r"\par\smallskip"]
    if solutions:
        lines.append(r"\textbf{" + heading + r"}\par")
    capacities = words("Capacity: leaf entries ", "Kapazität: Blatteinträge ", language) + str(exercise["leaf_capacity"])
    capacities += words("; internal child pointers ", "; innere Kindzeiger ", language) + str(exercise["internal_capacity"]) + "."
    operation = {"lookup": words("Lookup", "Suche", language), "range": words("Range", "Bereich", language),
                 "insert": words("Insert", "Einfügen", language), "delete": words("Delete", "Löschen", language)}[task["kind"]]
    operation += " " + (f"[{task['lower']}, {task['upper']}]" if task["kind"] == "range" else str(task["key"])) + ". "
    capacities = operation + capacities
    lines += [r"\fontsize{7.5}{9}\selectfont " + e(capacities) + r"\par\smallskip", diagram]
    legend = words("I: separators / child pages. L: entries / next leaf. Equality goes right.",
                   "I: Trennschlüssel / Kindseiten. L: Einträge / nächstes Blatt. Gleichheit führt nach rechts.", language)
    if mode == "map":
        legend += words(" Page map in depth order (d).", " Seitenplan nach Tiefe (d).", language)
    lines += [r"\fontsize{7}{8}\selectfont " + e(legend) + r"\par\smallskip"]
    if solutions:
        lines.append(r"\fontsize{8}{9.5}\selectfont")
        for step in _steps(exercise, answer, facts, language):
            lines.append(e(step) + r"\par")
        lines += [r"\smallskip " + e(localized(private["worked"]["explanation"], language)) + r"\par"]
    else:
        question = words("Record the path and returned entries.", "Notieren Sie Pfad und gefundene Einträge.", language)
        if task["kind"] == "range":
            question = words("Record the descent, scanned leaves and inclusive result.",
                             "Notieren Sie Abstieg, besuchte Blätter und das inklusive Ergebnis.", language)
        elif task["kind"] in ("insert", "delete"):
            question = words("Choose repairs; predict every final separator and the height.",
                             "Wählen Sie Reparaturen; bestimmen Sie alle Trennschlüssel und die Höhe.", language)
        lines += [r"\fontsize{8.5}{10}\selectfont " + e(question) + r"\par\medskip",
                  r"\noindent\textcolor{black!35}{\rule{\linewidth}{.3pt}}\par\vspace{3mm}",
                  r"\noindent\textcolor{black!35}{\rule{\linewidth}{.3pt}}\par"]
    # Refuse excessive scaling instead of silently creating unreadable slides.
    lines += [r"\end{minipage}\end{lrbox}",
              r"\ifdim\dimexpr\ht\bplusbox+\dp\bplusbox\relax>1.18\bplusheight",
              r"\PackageError{texstage-bplus-tree}{Prepared B+ material is too tall}{Use a taller box or shorten the title, prompt and explanation.}\fi",
              r"\makebox[\linewidth][c]{%",
              r"\ifdim\dimexpr\ht\bplusbox+\dp\bplusbox\relax>\bplusheight",
              r"\resizebox*{!}{\bplusheight}{\usebox{\bplusbox}}%",
              r"\else\usebox{\bplusbox}\fi}\endgroup"]
    return "\n".join(lines)


def prepare_lesson(source, context):
    # Author envelope and engine input have different byte limits.
    source = model.parse(model.canonical(source), byte_limit=20480)
    LESSON.validate(source)
    if type(source["format"]) is not int:
        raise model.InputError("lesson-format")
    for text in (source["title"], source["prompt"], source["worked"]["explanation"]):
        if any(any(ord(c) < 32 and c not in "\n\t" for c in value) for value in text.values()):
            raise model.InputError("control-character-in-text")
    exercise = model.source_for(source["exercise"])
    answer = model.answer_for(exercise, source["worked"]["answer"])
    facts = model.analyze(exercise, answer)
    required = ("path", "keys") if exercise["task"]["kind"] in ("lookup", "range") else ("path", "separators", "height")
    if facts["replay"]["state"] != "complete" or any(facts["claims"][name] is not True for name in required):
        raise model.InputError("Worked certificate must complete and every applicable prediction must be correct")
    public = {"format": 1, "title": copy.deepcopy(source["title"]), "prompt": copy.deepcopy(source["prompt"]),
              "exercise": copy.deepcopy(exercise), "interaction": "classroom"}
    private = {"exercise_digest": facts["exercise"], "feedback": source["feedback"],
               "worked": {"answer": copy.deepcopy(answer), "analysis": facts,
                          "explanation": copy.deepcopy(source["worked"]["explanation"])}}
    language = "de" if str(context.get("language", "en")).lower().split("-")[0] == "de" else "en"
    diagnostics = []
    if language == "de" and any("de" not in text for text in (source["title"], source["prompt"], source["worked"]["explanation"])):
        diagnostics.append("Missing German author text uses the required English text.")
    fragments = {edition: _fragment(public, private, language, edition == "solutions") for edition in ("exercise", "solutions")}
    if any(len(value.encode("utf-8")) > 128 * 1024 for value in fragments.values()):
        raise model.ResourceLimit("fragment-bytes")
    return PreparedAuthoring(PreparedItem(public=public, private=private,
        evaluations={"analysis": {"seed": model.canonical(exercise), "options": {}, "references": []}},
        diagnostics=diagnostics), fragments)
