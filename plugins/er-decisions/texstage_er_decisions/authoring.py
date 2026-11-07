# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""Prepared registration material from the frozen engine model and one source."""
import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from texstage.plugin_api.v1 import PreparedAuthoring, PreparedItem, latex_escape
from . import model

TYPE = "io.github.stefanjdecker.erdecisions.lesson"
ENGINE = "io.github.stefanjdecker.erdecisions.model"
ROOT = Path(__file__).resolve().parent
LESSON = Draft202012Validator(json.loads((ROOT / "schemas/lesson-v1.json").read_text(encoding="utf-8")))


def local(value, language):
    return value["de" if language.split("-")[0] == "de" else "en"]


def translated(en, de, language):
    return de if language.split("-")[0] == "de" else en


def require(ok, message):
    if not ok:
        raise ValueError(message)


def keyed(rows):
    result = {row["id"]: row for row in rows}
    require(len(result) == len(rows), "Repeated label or requirement ID")
    return result


def _masked_model(exercise):
    result = copy.deepcopy(exercise["model"])
    rel = result["relationship"]
    for decision in exercise["decisions"]:
        if decision["kind"] == "role-bounds":
            role = next(r for r in rel["roles"] if r["id"] == decision["target"])
            role.update(min=None, max=None)
        elif decision["kind"] == "attribute-owner":
            next(a for a in rel["attributes"] if a["id"] == decision["target"])["owner"] = None
        else:
            rel.update(form=None, pair_unique=None)
    return result


def _passed(facts):
    return facts["model_valid"] and all(c["admits"] == (c["expected"] == "allow") for c in facts["checks"])


def _bounds(role):
    return "?" if role["min"] is None else f'{role["min"]}..{"*" if role["max"] == "many" else role["max"]}'


def _names(public, language):
    return ({row["id"]: local(row["text"], language) for row in public["labels"]["entities"]},
            local(public["labels"]["relationship"], language),
            {row["id"]: local(row["text"], language) for row in public["labels"]["attributes"]})


def _decision(public, decision, language):
    entities, relationship, attributes = _names(public, language)
    rel = public["model"]["relationship"]
    role_names = {r["id"]: entities[r["entity"]] for r in rel["roles"]}
    if decision["kind"] == "role-bounds":
        title = translated("Links per ", "Verknüpfungen pro ", language) + role_names[decision["target"]]
        options = [_bounds(o["value"]) for o in decision["options"]]
    elif decision["kind"] == "attribute-owner":
        title = translated("Where does ", "Wohin gehört ", language) + attributes[decision["target"]] + translated(" belong?", "?", language)
        options = [relationship if o["value"] == "relationship" else role_names[o["value"]] for o in decision["options"]]
    else:
        title = translated("Representation of ", "Darstellung von ", language) + relationship
        options = [translated("Relationship", "Beziehung", language) if o["value"]["form"] == "relationship" else
                   translated("Entity + unique pair", "Entität + eindeutiges Paar", language) if o["value"]["pair_unique"] else
                   translated("Entity + ID only", "Entität + nur ID", language) for o in decision["options"]]
    return title, options


def _diagram(public, graph, language, width=".94"):
    """Trusted TikZ structure; all caller-authored labels are escaped plain text."""
    names, relationship, attributes = _names(public, language)
    rel = graph["relationship"]
    roles = rel["roles"]
    # Stable layout is semantic-role order, not source list order.
    left, right = roles
    attribute = rel["attributes"][0]
    # Permit Babel to hyphenate the first word in a fixed-width TikZ label.
    label = lambda text: r"\hspace{0pt}" + latex_escape(text)
    middle = ("diamond,aspect=2.8" if rel["form"] == "relationship" else
              "rectangle,dashed,rounded corners=2pt" if rel["form"] is None else "rectangle")
    suffix = " (?)" if rel["form"] is None else ""
    lines = [
        r"{\centering\resizebox{" + width + r"\linewidth}{!}{%",
        r"\begin{tikzpicture}[every node/.style={font=\small,align=center},line width=.5pt]",
        r"\node[draw," + middle + r",text width=2.6cm,inner sep=2pt,minimum height=.55cm] (middle) at (0,0) {" + label(relationship + suffix) + r"};",
        r"\node[draw,rectangle,text width=2.8cm,minimum height=.55cm,anchor=east,xshift=-.6cm] (left) at (middle.west) {" + label(names[left["entity"]]) + r"};",
        r"\node[draw,rectangle,text width=2.8cm,minimum height=.55cm,anchor=west,xshift=.6cm] (right) at (middle.east) {" + label(names[right["entity"]]) + r"};",
        r"\draw (left.east)--(middle.west); \draw (middle.east)--(right.west);",
    ]
    owner = attribute["owner"]
    text = attributes[attribute["id"]] + (" (?)" if owner is None else "")
    if owner == "relationship":
        attach = "middle"
    else:
        attach = "left" if owner == left["id"] else "right" if owner == right["id"] else None
    lines += [r"\node[draw,ellipse,font=\small,text width=2.6cm,inner sep=2pt,anchor=north,yshift=-.28cm] (attribute) at (" +
              (attach or "middle") + r".south) {" + label(text) + r"};"]
    if attach:
        lines.append(r"\draw (" + attach + r".south)--(attribute.north);")
    lines += [r"\end{tikzpicture}}\par}"]
    caption = " | ".join(translated("Per ", "Pro ", language) + names[r["entity"]] + ": " + _bounds(r)
                         for r in roles)
    lines.append(r"\centering\scriptsize " + label(caption) + r"\par\raggedright")
    if rel["form"] == "association-entity":
        count = translated("Each ", "Jede ", language) + relationship + translated(
            " has exactly one occupant of each role.", " hat genau einen Partner je Rolle.", language)
        uniqueness = translated("Pair unique.", "Paar eindeutig.", language) if rel["pair_unique"] else translated("Pair not constrained.", "Paar nicht eingeschränkt.", language)
        lines.append(r"\centering\scriptsize " + label(count + " " + uniqueness) + r"\par\raggedright")
    return "\n".join(lines)


def _records(snapshot):
    records = []
    for row in snapshot["links"]:
        roles = ", ".join(value for _, value in row["roles"])
        values = ", ".join(str(value).lower() if type(value) is bool else str(value) for _, value in row["values"])
        records.append(f'{row["id"]}: ({roles}) = {values}')
    return "; ".join(records) if records else "(no links)"


def _fragment(public, private, language, solutions):
    de = language.split("-")[0] == "de"
    title = local(public["title"], language)
    lines = [r"\begingroup\begin{lrbox}{\erdecisionsbox}\begin{minipage}{\linewidth}\raggedright\small",
             r"\textbf{\large " + latex_escape(title) + r"}\par\smallskip"]
    if public["points"]:
        label = (f"Live activity: {public['points']} points for a fully correct model." if not de else
                 f"Live-Aktivität: {public['points']} Punkte für ein vollständig korrektes Modell.")
        lines.append(r"\scriptsize " + latex_escape(label) + r"\par\smallskip")
    if not solutions:
        lines += [latex_escape(local(public["brief"], language)) + r"\par\medskip",
                  r"\begin{minipage}[t]{.46\linewidth}\scriptsize",
                  r"\textbf{" + ("Gegebene Anforderungen" if de else "Stated requirements") + r"}\par\smallskip"]
        for index, requirement in enumerate(public["requirements"], 1):
            lines.append(latex_escape(f"{index}. " + local(requirement["text"], language)) + r"\par\smallskip")
        lines += [r"\end{minipage}\hfill\begin{minipage}[t]{.50\linewidth}\scriptsize",
                  r"\textbf{" + ("Ihre Entscheidungen" if de else "Your decisions") + r"}\par\smallskip"]
        for index, decision in enumerate(public["decisions"], 1):
            title, options = _decision(public, decision, language)
            lines += [r"\textbf{" + latex_escape(f"{index}. {title}") + r"}\par",
                      latex_escape(" / ".join(options)) + r"\par\medskip"]
        lines += [r"\end{minipage}\par",
                  _diagram(public, public["model"], language, width=".80"),
                  r"\scriptsize " + latex_escape(
                      ("Beispiel: " if de else "Example: ") + _records(public["examples"][0])) + r"\par\smallskip",
                  latex_escape("Begründen Sie die Wahl. Mehrere Modelle sind möglich." if de else
                               "Explain your choices. More than one model can work.") + r"\par"]
    else:
        lines.append(r"\scriptsize\textbf{" + ("Geprüfte Alternativen" if de else "Checked alternatives") + r"}\par")
        for index, worked in enumerate(private["worked"], 1):
            if index > 1:
                lines.append(r"\hfill")
            lines += [r"\begin{minipage}[t]{.48\linewidth}",
                      _diagram(public, worked["model"], language),
                      r"\scriptsize " + latex_escape(f"{index}. " + local(worked["explanation"], language)) + r"\par",
                      r"\end{minipage}%"]
        lines.append(r"\par\medskip")
        lines.append(r"\scriptsize\textbf{" + ("Gegenbeispiele" if de else "Counterexamples") + r"}\par")
        for witness in private["teaching_witnesses"]:
            lines += [latex_escape(local(witness["explanation"], language)) + r"\par",
                      r"{\scriptsize " + latex_escape(_records(witness["snapshot"])) + r"}\par\smallskip"]
        lines.append(r"\scriptsize " + latex_escape(
            "Konsistent mit diesen Beispielen; kein allgemeiner Äquivalenzbeweis." if de else
            "Consistent with these examples; not a general equivalence proof.") + r"\par")
    # Measure the real content, not the host's fixed-height outer minipage.
    # Shrink only when needed, keeping the source's requested aspect ratio.
    lines += [r"\end{minipage}\end{lrbox}",
              r"\makebox[\linewidth][c]{%",
              r"\ifdim\dimexpr\ht\erdecisionsbox+\dp\erdecisionsbox\relax>\erdecisionsheight",
              r"\resizebox*{!}{\erdecisionsheight}{\usebox{\erdecisionsbox}}%",
              r"\else\usebox{\erdecisionsbox}\fi}",
              r"\endgroup"]
    return "\n".join(lines)


def prepare_lesson(source, context):
    source = copy.deepcopy(source)
    LESSON.validate(source)
    require(len(model.canonical(source)) <= 128 * 1024, "Lesson exceeds 128 KiB")
    # Validate the authoring envelope separately from the frozen engine seed.
    envelope = model.normalize({k: v for k, v in source.items() if k != "exercise"})
    exercise = model.source(source["exercise"])
    labels = envelope["labels"]
    entity_labels = keyed(labels["entities"])
    attribute_labels = keyed(labels["attributes"])
    german = keyed(envelope["requirements_de"])
    require(set(entity_labels) == set(exercise["model"]["entities"]), "Entity labels must cover the model exactly")
    attributes = exercise["model"]["relationship"]["attributes"]
    require(set(attribute_labels) == {a["id"] for a in attributes}, "Attribute labels must cover the model exactly")
    require(set(german) == {r["id"] for r in exercise["requirements"]}, "German requirements must cover the fixed requirements")
    require(len(exercise["decisions"]) <= 3 and len(attributes) == 1 and len(exercise["requirements"]) <= 4,
            "Prepared registration layout supports three decisions, one observed attribute and four requirements")
    require(all(len(value) <= 180 for value in exercise["brief"].values()), "Prepared brief must fit 180 characters per language")
    require(all(len(r["text"]) <= 160 for r in exercise["requirements"]), "Prepared requirements must fit 160 characters")
    shown = [copy.deepcopy(w) for w in exercise["snapshots"] if w["visibility"] == "public"]
    require(len(shown) == 1 and len(shown[0]["links"]) <= 2, "Prepared layout needs one public example with at most two links")
    require(shown[0]["expected"] == "allow", "The introductory public example must be permitted")
    labels["entities"].sort(key=lambda row: row["id"])
    labels["attributes"].sort(key=lambda row: row["id"])
    public = {
        "format": 1, "profile": exercise["format"], "id": exercise["id"], "title": envelope["title"],
        "brief": exercise["brief"], "labels": labels, "model": _masked_model(exercise),
        "requirements": [{"id": r["id"], "text": {"en": r["text"], "de": german[r["id"]]["text"]}} for r in exercise["requirements"]],
        "decisions": copy.deepcopy(exercise["decisions"]),
        "examples": [{k: v for k, v in shown[0].items() if k not in ("visibility", "expected", "requirements")}],
        "interaction": "decision-cards", "points": envelope.get("points", 0)
    }
    worked, identities = [], set()
    expected_answers = {model.canonical(a) for a in exercise["worked_answers"]}
    for row in envelope["solutions"]:
        answer = model.answer(row["answer"])
        identity = model.canonical(answer)
        require(identity not in identities, "Duplicate worked explanation")
        identities.add(identity)
        facts = model.analyze(exercise, answer)
        require(_passed(facts), "Worked explanation does not satisfy the exercise checks")
        worked.append({"answer": answer, "model": model.compile_model(exercise, answer),
                       "explanation": row["explanation"]})
    require(identities == expected_answers, "Explain exactly all configured worked alternatives")
    witnesses = []
    seen_witnesses = set()
    for row in envelope["counterexamples"]:
        answer = model.answer(row["answer"])
        facts = model.analyze(exercise, answer)
        require(facts["model_valid"], "Counterexample must use a well-formed candidate model")
        found = next((c for c in facts["checks"] if c["id"] == row["snapshot"]), None)
        require(found is not None and found["admits"] != (found["expected"] == "allow"),
                "Teaching witness must contradict the selected candidate")
        key = (row["snapshot"], model.canonical(answer))
        require(key not in seen_witnesses, "Duplicate teaching witness")
        seen_witnesses.add(key)
        snapshot = copy.deepcopy(next(w for w in exercise["snapshots"] if w["id"] == row["snapshot"]))
        require(len(snapshot["links"]) <= 2, "Prepared teaching witness needs at most two displayed links")
        witnesses.append({"answer": answer, "snapshot": snapshot, "finding": found, "explanation": row["explanation"]})
    private = {"exercise_digest": model.digest(model.semantic_seed(exercise)), "worked": worked,
               "teaching_witnesses": witnesses,
               "checks": [{"id": w["id"], "expected": w["expected"]} for w in exercise["snapshots"]]}
    language = context.get("language", "en")
    fragments = {edition: _fragment(public, private, language, edition == "solutions")
                 for edition in ("exercise", "solutions")}
    require(all(len(text.encode("utf-8")) <= 128 * 1024 for text in fragments.values()), "Prepared fragment exceeds host budget")
    return PreparedAuthoring(
        PreparedItem(public=public, private=private,
                     evaluations={"analysis": {"seed": json.dumps(exercise, ensure_ascii=False, sort_keys=True,
                                                                   separators=(",", ":"), allow_nan=False),
                                                "options": {}, "references": []}},
                     diagnostics=[]),
        fragments)
