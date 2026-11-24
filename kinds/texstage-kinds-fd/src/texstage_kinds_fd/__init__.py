# SPDX-FileCopyrightText: 2026 Stefan Decker
# SPDX-License-Identifier: Apache-2.0
"""An activity for the closure of a set of attributes under functional dependencies."""
from __future__ import annotations

import re

from texstage.activities import Built, Check, Entry, Kind, Message, Unbuildable, Unfit, fixed
from texstage.activities.options import InBody, Words

NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
TEXT_LIMIT = 100  # TeXStage's short-text input, also on phones.


def closure(start, dependencies):
    """Apply every enabled dependency until a complete pass adds no attributes."""
    known = set(start)
    while True:
        size = len(known)
        for lhs, rhs in dependencies:
            if lhs <= known:
                known.update(rhs)
        if len(known) == size:
            return known


def _key(names, attributes):
    """Use schema order for groups, private references and portable answer keys."""
    return ",".join(name for name in attributes if name in names) or "{}"


def _answer(text, attributes):
    """Read one set, with optional braces and whitespace or commas between names."""
    text = text.strip()
    if text == "∅":
        return "{}", None
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()
        if not text:
            return "{}", None
    members = set()
    for group in text.split(","):
        names = group.split()
        if not names or any(not NAME.fullmatch(name) for name in names):
            return None, Message("setSyntax")
        for name in names:
            if name not in attributes:
                return None, Message("unknownAttribute", {"name": name})
            members.add(name)
    return _key(members, attributes), None


def _declared(names, attributes, option):
    for name in names:
        if name not in attributes:
            raise Unbuildable(f"{option}= names an attribute outside the schema: {name}")
    return set(names)


class AttributeClosure(Kind):
    NAME = "fd-closure"
    API = 1
    INPUT = "text"
    REDUCTION = "groups"
    OPTIONS = fixed(attributes=Words(), dependencies=Words(longest=2 * TEXT_LIMIT + 4),
                    start=Words(), reference=InBody())
    MESSAGES = fixed(setSyntax=(), unknownAttribute=("name",))

    def build(self, options, bodies):
        attributes = options["attributes"]
        if not attributes or any(not NAME.fullmatch(name) for name in attributes):
            raise Unbuildable("attributes= needs names beginning with a letter, using ASCII letters, digits or underscores")
        if len(set(attributes)) != len(attributes):
            raise Unbuildable("attributes= repeats a name")
        if len(",".join(attributes)) > TEXT_LIMIT:
            raise Unbuildable(f"the comma-separated attribute names must fit the phone's {TEXT_LIMIT}-character answer")

        start = _declared(options["start"], attributes, "start")
        dependencies = []
        for rule in options["dependencies"]:
            sides = rule.split("->")
            if len(sides) != 2 or not sides[1].strip():
                raise Unbuildable(f"dependencies= expects LHS -> RHS with at least one attribute on the right: {rule}")
            lhs, rhs = (_declared(side.split(), attributes, "dependencies") for side in sides)
            dependencies.append((lhs, rhs))
        expected = _key(closure(start, dependencies), attributes)
        options["reference"]
        for reference in bodies.get("references", []):
            if _answer(reference, attributes)[0] != expected:
                raise Unbuildable(f"the supplied reference disagrees with the computed closure {expected}")
        return Built({"attributes": attributes}, {"reference": [expected]})

    def normalize(self, step, entry):
        if not isinstance(entry.text, str):
            raise TypeError("an attribute set is a text entry")
        text = entry.text.strip()
        if not text:
            raise Unfit("enter an attribute set", "text")
        if len(text) > TEXT_LIMIT:
            raise Unfit(f"at most {TEXT_LIMIT} characters", "too-long")
        key, _ = _answer(text, step.item["attributes"])
        return Entry(text=key or text)

    def check(self, prepared, step, entry):
        if not isinstance(entry.text, str):
            raise TypeError("an attribute set is a text entry")
        if len(entry.text) > TEXT_LIMIT:
            return Check("invalid", message=Message("setSyntax"))
        key, message = _answer(entry.text, step.item["attributes"])
        if message:
            return Check("invalid", message=message)
        return Check("ok", key=key)
