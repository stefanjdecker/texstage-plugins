# SPDX-License-Identifier: Apache-2.0
"""Prepare public exercises, private references and static editions from one source."""
import copy
import json
import re

from texstage.plugin_api.v1 import PreparedAuthoring, PreparedItem, latex_escape
from . import model

PROVIDER = "io.github.stefanjdecker.queryplan"
ENGINE = PROVIDER + ".cost"
TYPE = PROVIDER + ".challenge"

WORDS = {
    "en": {
        "query": "Fixed query", "output": "Output (keep duplicates)", "joins": "Joins",
        "filters": "Filters", "none": "None", "statistics": "Estimated statistics",
        "legend": "N: base rows; P: pages; R: filtered rows; W: row bytes.",
        "subsets": "Joined row estimates", "index": "Available equality index",
        "memory": "Hash workspace per operator", "rules": "Cost rules",
        "units": "Teaching cost units, not elapsed time.",
        "best": "Find a minimum-cost legal plan.", "budget": "Find a legal plan costing at most",
        "baseline": "Starting plan", "worked": "One worked plan", "optimal": "An optimal reference",
        "node": "Node", "local": "Local cost", "total": "Subtree cost", "root": "Total cost",
        "scan": "scan", "seq": "sequential", "index_scan": "index",
        "nested": "nested loop", "hash-left": "hash (build left)", "hash-right": "hash (build right)",
        "children": "inputs", "rows": "output rows", "minimum": "Minimum in this plan family",
        "ties": "Tied optimal plans", "explain": "Explain the choice",
        "question": "Choose the scans, join order and join methods. Justify your plan.",
        "hash": "Hash needs B(W+16) bytes. A non-fitting hash is unavailable.",
        "formula": "Scan: 100P+N. Index: 400(H+R)+R. Nested: LR+O. Hash: 2B+Q+O.",
        "notation": "H: index height; L/R: child rows; B/Q: build/probe rows; O: output rows. Intermediate widths add.",
        "cumulative": "Add child totals once. Do not add all subtree costs.",
        "bag": "Projection keeps duplicate occurrences.", "reference_note": "Every tied optimum is accepted.",
    },
    "de": {
        "query": "Feste Anfrage", "output": "Ausgabe (Duplikate behalten)", "joins": "Verknüpfungen",
        "filters": "Filter", "none": "Keine", "statistics": "Geschätzte Statistik",
        "legend": "N: Basiszeilen; P: Seiten; R: gefilterte Zeilen; W: Zeilenbytes.",
        "subsets": "Geschätzte Verbundzeilen", "index": "Verfügbarer Gleichheitsindex",
        "memory": "Hash-Arbeitsspeicher je Operator", "rules": "Kostenregeln",
        "units": "Kosten dieses Lehrmodells, keine Laufzeit.",
        "best": "Finden Sie einen zulässigen Plan mit minimalen Kosten.",
        "budget": "Finden Sie einen zulässigen Plan mit Kosten bis",
        "baseline": "Ausgangsplan", "worked": "Ein Lösungsplan", "optimal": "Eine optimale Referenz",
        "node": "Knoten", "local": "Lokale Kosten", "total": "Teilbaumkosten", "root": "Gesamtkosten",
        "scan": "Scan", "seq": "sequenziell", "index_scan": "Index",
        "nested": "Nested Loop", "hash-left": "Hash (links aufbauen)", "hash-right": "Hash (rechts aufbauen)",
        "children": "Eingaben", "rows": "Ausgabezeilen", "minimum": "Minimum dieser Planfamilie",
        "ties": "Gleichwertige optimale Pläne", "explain": "Begründung",
        "question": "Wählen Sie Scans, Join-Reihenfolge und Join-Verfahren. Begründen Sie Ihren Plan.",
        "hash": "Hash benötigt B(W+16) Bytes. Bei zu wenig Speicher ist Hash unzulässig.",
        "formula": "Scan: 100P+N. Index: 400(H+R)+R. Nested: LR+O. Hash: 2B+Q+O.",
        "notation": "H: Indexhöhe; L/R: Kindzeilen; B/Q: Build-/Probe-Zeilen; O: Ausgabezeilen. Zeilenbreiten addieren sich.",
        "cumulative": "Kindkosten einmal addieren. Nicht alle Teilbaumkosten summieren.",
        "bag": "Die Projektion behält Duplikate.", "reference_note": "Jedes gleichwertige Optimum wird akzeptiert.",
    },
}
# Standard pdfLaTeX/T1 examples use this small, explicit text repertoire.
LATIN = set("äöüÄÖÜßéèêëáàâãåÁÀÂÃÅÉÈÊËíìîïÍÌÎÏóòôõÓÒÔÕúùûÚÙÛñÑçÇøØæÆœŒ")


def _pdf_text(value):
    """Never interpret author strings as TeX; make other Unicode explicit."""
    text = str(value)
    shown = "".join(c if 32 <= ord(c) < 127 or c in LATIN else
                    (" " if c in "\n\r\t" else f"[U+{ord(c):04X}]") for c in text)
    # Bound unbreakable runs without ever splitting an escaped TeX command.
    return "".join(latex_escape(part) + (r"\allowbreak{}" if len(part) == 24 and not part.isspace() else "")
                   for part in re.findall(r"\s+|\S{1,24}", shown))


def _mono(value):
    # Dots and underscores are safe discretionary breakpoints for qualified IDs.
    rendered = _pdf_text(value).replace(".", r".\allowbreak{}").replace(r"\_", r"\_\allowbreak{}")
    return r"\texttt{" + rendered + "}"


def _heading(label):
    return r"\par\smallskip\textbf{" + _pdf_text(label) + r"}\par"


def _number(value):
    return str(value)


def _query(exercise, w):
    query = exercise["query"]
    rows = [_heading(w["query"]), _pdf_text(w["output"]) + ": " +
            ", ".join(_mono(".".join(ref)) for ref in query["output"]) + r".\par"]
    rows.append(_pdf_text(w["joins"]) + ": ")
    if query["joins"]:
        rows.extend(_mono(".".join(j["left"])) + " = " + _mono(".".join(j["right"])) + r"\par"
                    for j in query["joins"])
    else:
        rows.append(_pdf_text(w["none"]) + r".\par")
    rows.append(_pdf_text(w["filters"]) + ": ")
    filters = []
    for r in query["relations"]:
        if "filter" in r:
            f = r["filter"]
            literal = json.dumps(f["value"], ensure_ascii=True)
            filters.append(_mono(r["id"] + "." + f["column"]) + " = " + _mono(literal))
    rows.append((r";\quad ".join(filters) if filters else _pdf_text(w["none"])) + r".\par")
    return "\n".join(rows)


def _statistics(exercise, w):
    cards = {tuple(c["relations"]): c["rows"] for c in exercise["statistics"]["cardinalities"]}
    lines = [_heading(w["statistics"]),
             r"\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.1}",
             r"\begin{tabularx}{\linewidth}{@{}Xrrrr@{}}",
             r"\textbf{Relation} & \textbf{N} & \textbf{P} & \textbf{R} & \textbf{W}\\\hline"]
    for row in exercise["statistics"]["base"]:
        values = [row["rows"], row["pages"], cards[(row["relation"],)], row["row_bytes"]]
        lines.append(_mono(row["relation"]) + " & " + " & ".join(_number(v) for v in values) + r"\\")
    lines += [r"\end{tabularx}\par", _pdf_text(w["legend"]) + r"\par"]
    joined = [c for c in exercise["statistics"]["cardinalities"] if len(c["relations"]) > 1]
    if joined:
        lines.append(_heading(w["subsets"]))
        lines.extend(" + ".join(_mono(n) for n in c["relations"]) + ": " +
                     _number(c["rows"]) + r"\par" for c in joined)
    indexes = [r for r in exercise["query"]["relations"] if "index" in r]
    lines.append(_heading(w["index"]))
    if indexes:
        for r in indexes:
            lines.append(_mono(r["id"] + "." + r["index"]["column"]) +
                         f' (H={r["index"]["height"]})' + r"\par")
    else:
        lines.append(_pdf_text(w["none"]) + r".\par")
    return "\n".join(lines)


def _plan(answer, facts, w):
    lines = []
    for i, node in enumerate(answer["nodes"]):
        prefix = r"\textbf{" + str(i + 1) + "}. "
        if node["op"] == "scan":
            detail = _pdf_text(w["seq"] if node["method"] == "seq" else w["index_scan"]) + " " + \
                     _pdf_text(w["scan"]) + " " + _mono(node["relation"])
        else:
            detail = _pdf_text(w[node["method"]]) + "; " + _pdf_text(w["children"]) + \
                     f' {node["left"] + 1}, {node["right"] + 1}'
        lines.append(prefix + detail + r"\par")
    lines += [r"\smallskip\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrr@{}}",
              _pdf_text(w["node"]) + " & " + _pdf_text(w["local"]) + " & " + _pdf_text(w["total"]) + r"\\\hline"]
    for node in facts["nodes"]:
        # Ungrouped exact integers keep even the 13-digit bound inside the table.
        lines.append(f'{node["node"] + 1} & {node["local_cost"]} & {node["total_cost"]}' + r"\\")
    lines += [r"\end{tabular*}\par", r"\smallskip\textbf{" + _pdf_text(w["root"]) + ": " +
              _number(facts["cost"]) + r"}\par"]
    return "\n".join(lines)


def _short_plan(answer, w):
    lines = []
    for i, node in enumerate(answer["nodes"]):
        if node["op"] == "scan":
            text = _pdf_text(w["seq"] if node["method"] == "seq" else w["index_scan"]) + " " + _mono(node["relation"])
        else:
            text = _pdf_text(w[node["method"]]) + f' ({node["left"] + 1}, {node["right"] + 1})'
        lines.append(str(i + 1) + ": " + text)
    return r";\quad ".join(lines) + r".\par"


def _fragment(prepared, language, solutions):
    w = WORDS[language]
    source = prepared["source"]
    exercise, reference = source["exercise"], prepared["reference"]
    goal = (w["best"] if source["goal"]["kind"] == "best" else
            w["budget"] + " " + _number(source["goal"]["max_cost"]) + ".")
    scoring = (("Live activity: " + str(source["points"]) + " points for meeting the target.") if language == "en" else
               ("Live-Aktivitaet: " + str(source["points"]) + " Punkte beim Erreichen des Ziels.")) if source["points"] else ""
    lines = [r"\begingroup",
             r"\begin{adjustbox}{max totalsize={\linewidth}{\csname queryplan@height\endcsname},center}",
             r"\begin{minipage}{\linewidth}\raggedright\scriptsize",
             r"\textbf{" + _pdf_text(goal) + r"}\par",
             _pdf_text(w["units"]) + r"\par " + (_pdf_text(scoring) + r"\par " if scoring else "") + r"\smallskip",
             r"\begin{minipage}[t]{.58\linewidth}\raggedright\vspace{0pt}",
             _query(exercise, w), _statistics(exercise, w),
             _heading(w["rules"]), _pdf_text(w["formula"]) + r"\par",
             _pdf_text(w["notation"]) + r"\par",
             r"\end{minipage}\hfill\begin{minipage}[t]{.39\linewidth}\raggedright\vspace{0pt}"]
    if solutions:
        lines += [_heading(w["worked"]), _plan(source["worked_answer"], prepared["worked"], w),
                  _heading(w["explain"]), _pdf_text(source["explanation"][language]) + r"\par",
                  r"\smallskip " + _pdf_text(w["minimum"]) + ": " + _number(reference["cost"]) + r".\par",
                  _pdf_text(w["ties"]) + ": " + str(reference["count"]) + r".\par",
                  _pdf_text(w["reference_note"]) + r"\par"]
        if prepared["worked"]["cost"] != reference["cost"]:
            lines += [_heading(w["optimal"]), _short_plan(reference["plan"], w)]
    else:
        lines += [_heading(w["baseline"]), _plan(source["baseline"], prepared["baseline"], w),
                  r"\smallskip " + _pdf_text(w["question"]) + r"\par"]
    lines += [_heading(w["memory"]), _number(exercise["limits"]["hash_bytes"]) + r" bytes.\par",
              _pdf_text(w["hash"]) + r"\par\smallskip",
              _pdf_text(w["cumulative"]) + r"\par",
              r"\end{minipage}\par\end{minipage}\end{adjustbox}\endgroup"]
    return "\n".join(lines)


def prepare_lesson(source, context):
    """The only reference search happens here, once per preparation."""
    prepared = model.prepare_reference(source)
    normalized = prepared["source"]
    language = "de" if str(context.get("language", "en")).lower().split("-")[0] == "de" else "en"
    exercise = normalized["exercise"]
    public = {"format": 1, "exercise": copy.deepcopy(exercise),
              "baseline": copy.deepcopy(normalized["baseline"]),
              "baseline_analysis": copy.deepcopy(prepared["baseline"]),
              "goal": copy.deepcopy(normalized["goal"]), "points": normalized["points"]}
    private = {"exercise": prepared["worked"]["exercise"], "reference": copy.deepcopy(prepared["reference"]),
               "worked": {"answer": copy.deepcopy(normalized["worked_answer"]),
                          "analysis": copy.deepcopy(prepared["worked"]),
                          "explanation": copy.deepcopy(normalized["explanation"])}}
    fragments = {edition: _fragment(prepared, language, edition == "solutions")
                 for edition in ("exercise", "solutions")}
    if any(len(value.encode("utf-8")) > 128 * 1024 for value in fragments.values()):
        raise model.ResourceLimit("fragment-bytes")
    return PreparedAuthoring(
        prepared=PreparedItem(public=public, private=private,
            evaluations={"analysis": {"seed": model.canonical(exercise), "options": {}, "references": []}}),
        fragments=fragments)
