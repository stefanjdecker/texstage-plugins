# SPDX-License-Identifier: Apache-2.0
"""One reviewed source supplies private checks, public material and static TeX."""
import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from texstage.plugin_api.v1 import PreparedAuthoring, PreparedItem, latex_escape
from . import model

ENGINE = "io.github.stefanjdecker.relationallab.algebra"
TYPE = "io.github.stefanjdecker.relationallab.tree"
ROOT = Path(__file__).resolve().parent
LESSON = Draft202012Validator(json.loads((ROOT / "schemas/lesson-v1.json").read_text(encoding="utf-8")))


def localized(value, language):
    return value["de" if language.split("-")[0] == "de" else "en"]


def _expected(exercise):
    tree = exercise.get("reference_tree", exercise.get("baseline_tree"))
    budget = model.Budget()
    facts, public_cells = [], None
    for instance in sorted(exercise["instances"], key=lambda row: row["id"]):
        relation, stats = model.evaluate_tree(exercise, tree, instance, budget)
        facts.append(relation.facts(instance["id"]))
        if instance["visibility"] == "public":
            public_cells = stats["cells"]
    return facts, public_cells


def _cell(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return latex_escape(str(value))


def _tables(public):
    # Two columns keep the small teaching datasets readable on a slide.
    tables = []
    for name, columns in sorted(public["relations"].items()):
        rows = public["instance"]["tables"][name]
        header = " & ".join(r"\textbf{" + latex_escape(c[0]) + "}" for c in columns)
        table = [r"\begin{minipage}[t]{.48\linewidth}\centering\scriptsize",
                 r"\textbf{" + latex_escape(name) + r"}\par\smallskip",
                 r"\setlength{\tabcolsep}{3pt}\begin{tabular}{" + "l" * len(columns) + "}",
                 header + r"\\\hline"]
        table += [" & ".join(_cell(value) for value in row) + r"\\" for row in rows]
        if not rows:
            table.append(r"\multicolumn{" + str(len(columns)) + r"}{c}{(empty)}\\")
        table += [r"\end{tabular}\end{minipage}"]
        tables.append("\n".join(table))
    return r"\par\medskip".join(r"\hfill".join(tables[i:i + 2]) for i in range(0, len(tables), 2))


def _tree_lines(tree):
    lines = []
    for i, node in enumerate(tree):
        op = node[0]
        if op == "rel":
            text = f"{i}: relation {node[1]}"
        else:
            text = f"{i}: {op} " + model.canonical(node[1:])
        lines.append(r"\mbox{\ttfamily " + latex_escape(text) + r"}\par")
    return "\n".join(lines)


def _fragment(public, worked, language, *, solutions):
    de = language.split("-")[0] == "de"
    title = localized(public["title"], language)
    prompt = localized(public["prompt"], language)
    rows = [r"\begingroup\raggedright\small",
            r"\textbf{" + latex_escape(title) + r"}\par",
            latex_escape(prompt) + r"\par\smallskip"]
    if solutions:
        label = "Eine mögliche Lösung" if de else "One worked answer"
        rows += [r"\textbf{" + label + r"}\par\scriptsize",
                 _tree_lines(worked["tree"]),
                 r"\smallskip\normalsize " + latex_escape(localized(worked["explanation"], language)) + r"\par"]
        if public["mode"] == "rewrite":
            rows += [r"\smallskip\scriptsize " + latex_escape(
                ("Zwischenzellen: " if de else "Intermediate output cells: ") +
                f'{worked["baseline_cells"]} -> {worked["cells"]}.') + r"\par"]
            for n, step in enumerate(worked["answer"]["steps"], 1):
                rows.append(latex_escape(f'{n}. {step["rule"]} @ {step["path"]}') + r"\par")
        else:
            rows.append(r"\smallskip\scriptsize " + latex_escape(
                "Geprüft auf den konfigurierten Beispieldaten; kein allgemeiner Äquivalenzbeweis." if de else
                "Checked on the configured instances; this is not a general equivalence proof.") + r"\par")
    else:
        rows += [_tables(public), r"\par\medskip"]
        if public["mode"] == "rewrite":
            rows += [r"\scriptsize\textbf{" + ("Ausgangsbaum" if de else "Starting tree") + r"}\par",
                     _tree_lines(public["baseline_tree"])]
        else:
            rows.append(latex_escape(
                "Konstruieren Sie einen Anfragebaum. Projektion entfernt Duplikate." if de else
                "Construct a query tree. Projection removes duplicate tuples.") + r"\par")
    rows.append(r"\endgroup")
    return "\n".join(rows)


def prepare_lesson(source, context):
    # The authoring envelope extends the lesson, not the frozen engine seed.
    source = copy.deepcopy(source)
    LESSON.validate(source)
    source["explanation"] = model.parse(model.canonical(source["explanation"]), limit=16384)
    exercise = model.source(source["exercise"])
    mode = exercise["task"]["mode"]
    answer = model.answer(source["worked_answer"])
    if answer["mode"] != mode:
        raise ValueError("Worked answer mode differs from the exercise")
    expected, baseline_cells = _expected(exercise)
    facts = model.analyze(exercise, answer)
    if not facts["valid"] or facts["fixtures"] != expected:
        raise ValueError("Worked answer does not satisfy the configured instances")
    if mode == "rewrite" and (not facts["proof"]["verified"] or not facts["proof"]["steps"] or
                              not facts["proof"]["improved"]):
        raise ValueError("Worked rewrite must verify and reduce public intermediate output cells")
    public = {k: copy.deepcopy(exercise[k]) for k in ("id", "title", "prompt", "relations", "task")}
    public.update(mode=mode, instance=copy.deepcopy(next(i for i in exercise["instances"] if i["visibility"] == "public")),
                  initial_tree=copy.deepcopy(exercise.get("initial_tree", [])),
                  sharing_notice={"en": "The presenter can share a saved answer with the class without your name.",
                                  "de": "Die Lehrperson kann eine gespeicherte Antwort ohne Ihren Namen mit der Gruppe teilen."})
    if mode == "rewrite":
        public["baseline_tree"] = copy.deepcopy(exercise["baseline_tree"])
    tree = answer.get("tree", facts.get("proof", {}).get("tree"))
    worked = {"answer": answer, "tree": tree, "explanation": source["explanation"],
              "cells": facts["public"]["cells"], "baseline_cells": baseline_cells}
    private = {"exercise": model.source_identity(exercise), "expected": expected,
               "baseline_cells": baseline_cells, "worked": worked}
    diagnostics = [f'Duplicate tuples normalized to set semantics: {r["instance"]}/{r["relation"]} ({r["duplicate_rows"]}).'
                   for r in model.source_diagnostics(exercise)]
    language = context.get("language", "en")
    # Keep Unicode seed text compact; the seed's 64 KiB UTF-8 limit still applies.
    seed = json.dumps(exercise, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(seed.encode("utf-8")) > 65536:
        raise model.ResourceLimit("seed-bytes")
    return PreparedAuthoring(
        PreparedItem(public=public, private=private,
                     evaluations={"analysis": {"seed": seed, "options": {}, "references": []}},
                     diagnostics=diagnostics),
        {edition: _fragment(public, worked, language, solutions=edition == "solutions")
         for edition in ("exercise", "solutions")})
