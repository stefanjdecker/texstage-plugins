# SPDX-License-Identifier: Apache-2.0
"""Checked, one-source live activities and exercise/solution TeX fragments."""
import copy

from texstage.plugin_api.v1 import PreparedAuthoring, PreparedItem, latex_escape
from .model import check_lesson
from .validation import bounded, canonical

ENGINE = "io.github.stefanjdecker.normalizationworkshop.analyze"
TYPE = "io.github.stefanjdecker.normalizationworkshop.workshop"


def local(value, language):
    return value["de" if str(language).split("-")[0] == "de" else "en"]


def attributes(mask, ids):
    return ", ".join(a for i, a in enumerate(ids) if mask & (1 << i)) or "{}"


def fd_text(pair, ids):
    return attributes(pair[0], ids) + " -> " + attributes(pair[1], ids)


def answer_text(answer, ids):
    if answer["mode"] == "classify":
        result = answer["normal_form"].upper()
        if answer["witness"] is not None:
            result += "; " + fd_text(answer["witness"], ids)
        return result
    return "; ".join(f"R{i}({attributes(mask, ids)})"
                     for i, mask in enumerate(answer["relations"], 1))


def _fragment(public, worked, language, *, solutions):
    de = str(language).startswith("de")
    ids = [a["id"] for a in public["attributes"]]
    rows = [r"\begingroup\raggedright\small",
            r"\textbf{" + latex_escape(local(public["title"], language)) + r"}\par",
            latex_escape(local(public["prompt"], language)) + r"\par\smallskip"]
    if solutions:
        rows += [r"\textbf{" + ("Eine mögliche Lösung" if de else "One worked answer") + r"}\par",
                 latex_escape(answer_text(worked["answer"], ids)) + r"\par\smallskip",
                 latex_escape(local(worked["explanation"], language)) + r"\par"]
    else:
        rows += [r"\textbf{R(" + latex_escape(", ".join(ids)) + r")}\par",
                 r"{\scriptsize " + latex_escape("; ".join(
                     a["id"] + ": " + local(a["label"], language) for a in public["attributes"])) + r"}\par\smallskip",
                 latex_escape("; ".join(fd_text(fd, ids) for fd in public["fds"]) or
                              ("Keine nichttrivialen FDs." if de else "No nontrivial FDs.")) + r"\par\smallskip"]
        task = public["task"]
        if task["mode"] == "classify":
            help_text = ("Höchste Normalform wählen. Unterhalb BCNF: eine FD angeben, die die nächste Normalform verletzt."
                         if de else "Choose the highest normal form. Below BCNF, give an FD that violates the next normal form.")
        else:
            help_text = (f'Zerlegen Sie verlustfrei in {task["target"].upper()}. ' if de else
                         f'Decompose losslessly into {task["target"].upper()}. ')
            help_text += (("FD-Erhaltung ist erforderlich." if task["preserve"] else "FD-Erhaltung prüfen und diskutieren.")
                          if de else ("Preserve all FDs." if task["preserve"] else "Check and discuss FD preservation."))
        rows += [latex_escape(help_text) + r"\par",
                 r"\smallskip\scriptsize " + latex_escape(
                     "Alle Attribute haben atomare Werte (1NF)." if de else
                     "All attributes have atomic values (1NF).") + r"\par"]
    return "\n".join(rows + [r"\endgroup"])


def prepare_lesson(source, context):
    source = bounded(copy.deepcopy(source))
    checked = check_lesson(source)  # Refuse an impossible or incorrect worked answer.
    public = {key: copy.deepcopy(source["exercise"][key])
              for key in ("id", "title", "prompt", "attributes", "task")}
    public["fds"] = checked["seed"]["fds"]
    public["sharing_notice"] = {
        "en": "Your saved answer may be shared with the class without your name. Feedback appears after reveal.",
        "de": "Ihre gespeicherte Antwort kann ohne Ihren Namen geteilt werden. Rückmeldung erscheint nach der Auflösung."}
    worked = {"answer": checked["answer"], "explanation": source["explanation"]}
    private = {"seed": checked["seed"], "worked": worked, "language": context.get("language", "en")}
    language = context.get("language", "en")
    return PreparedAuthoring(
        PreparedItem(public=public, private=private,
                     evaluations={"analysis": {"seed": canonical(checked["seed"]), "options": {}, "references": []}},
                     diagnostics=checked["diagnostics"]),
        {edition: _fragment(public, worked, language, solutions=edition == "solutions")
         for edition in ("exercise", "solutions")})
