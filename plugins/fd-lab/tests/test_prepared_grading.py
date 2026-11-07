# SPDX-License-Identifier: Apache-2.0
"""Prepared grading agrees with full analysis, without accepting browser grades."""
import importlib.util
from pathlib import Path

import pytest
from texstage.plugins import PluginError
from texstage_fd_lab import model
from texstage_fd_lab.grading import grade, feedback
from test_lesson import provider, runtime, source, prepared, envelope, worked

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("fd_classroom_cases", ROOT / "maintenance/fd_classroom_cases.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


@pytest.mark.parametrize("mode,count", [("practice",600),("keys_all",600),("refuted",600),
    ("keys_one",10),("implied",50),("different_sizes",10),("empty_key",3)])
def test_prepared_checks_match_independent_analysis_and_certificate_verification(provider, mode, count):
    item = prepared(mode)["prepared"]
    assert item["evaluations"] == {}
    cases = generator.cases(source(mode), count, diverse=True)
    assert len({model.canonical(c["answer"]) for c in cases}) == count
    for case in cases:
        answer = case["answer"]
        checked = grade(item["public"], item["private"], answer)
        analysis = model.analyze(item["public"]["seed"], answer)
        slot = {"answer": answer, "digest": model.digest(["fd-answer-v1",answer])}
        assert checked == feedback(item["public"], item["private"], slot, {"status":"ok","data":analysis})
        assert checked["correct"] is case["correct"]


@pytest.mark.parametrize("injected", [{"correct":True}, {"credit":1000}, {"points":100},
                                      {"feedback":{"correct":True}}, {"facts":{}}])
def test_student_cannot_supply_grades_or_private_checks(runtime, injected):
    r = runtime
    assert r.command("lesson","teacher","presenter",envelope("open",{"control":0}))["accepted"]
    payload = {"phase":1,"version":0,"answer":worked()} | injected
    with pytest.raises(PluginError):
        r.command("lesson","alice","participant",envelope("submit",payload,"attack000001"))
    assert r.db.execute("SELECT count(*) FROM actor_records").fetchone()[0] == 0
    assert r.db.execute("SELECT count(*) FROM point_credits").fetchone()[0] == 0
