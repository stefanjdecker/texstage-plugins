# SPDX-License-Identifier: Apache-2.0
"""Persist every accepted prediction exactly, including wrong boundary answers."""
import copy
import itertools

from texstage_bplus_lab import model
from texstage_bplus_lab.state import FEEDBACK_RESERVE, MAX_ACTORS, SLOT_BYTES, STATE_BYTES
from texstage_bplus_lab.storage import pack_answer, unpack_answer, pack_feedback, unpack_feedback, read_slot, write_slot, reserve_slot, REASONS
from test_state import source


def test_boundary_predictions_round_trip_and_fit_1000_host_records():
    assert MAX_ACTORS == 1000
    assert SLOT_BYTES <= 4096 and STATE_BYTES <= 224 * 1024
    for name in ("lookup", "range", "insert", "delete"):
        seed = source(name)["exercise"]
        for key, node, count in itertools.product((-9999, 0, 9999), (0, 63), (0, 1)):
            answer = {"format": 1, "path": [node] * 3}
            if name in ("lookup", "range"):
                answer["keys"] = [key] * ((40 if name == "range" else 1) * count)
                if name == "range": answer["leaves"] = [node] * 20
            else:
                answer.update(repairs=[{"op": "split", "node": node, "left_count": 6, "separator": key}] * (3 * count),
                              separators=[{"node": node, "keys": [key] * 5}] * (10 * count), height=3)
            model.answer_for(seed, answer)  # Includes valid syntax with invalid mathematics.
            before = copy.deepcopy(answer)
            packed = pack_answer(answer)
            assert unpack_answer(packed) == answer == before
            slot = write_slot({"version": 1_000_000_000, "answer": answer, "epoch": 9007199254740991,
                               "correlation": "x" * 64, "status": "unavailable"})
            assert read_slot(slot)["answer"] == answer
            slot = reserve_slot(slot, 1_000_000_000, FEEDBACK_RESERVE)
            assert len(model.canonical({"x" * 64: slot})) <= SLOT_BYTES
            unpack_answer(packed)["path"].append(7)
            assert unpack_answer(packed) == answer
    for op in ("borrow", "merge"):
        answer = source("delete")["worked"]["answer"]
        answer["repairs"] = [{"op": op, "node": 63, "sibling": 63}] * 3
        assert unpack_answer(pack_answer(answer)) == answer


def test_every_feedback_variant_is_lossless_with_reserved_room():
    variants = [{"code": "unavailable", "reason": r} for r in ("binding", "evaluation", "facts", "identity")]
    for reason in REASONS:
        for node in (None, 0, 63):
            variants.append({"code": "revise", "correct": False, "reason": reason,
                             "checked_repairs": 3, "at": 20, "node": node})
    for bits in itertools.product((False, True), repeat=3):
        failed = [k for k, b in zip(("keys", "separators", "height"), bits) if b]
        variants.append({"code": "revise" if failed else "correct", "correct": not failed,
                         "reason": "prediction" if failed else "complete", "failed": failed, "checked_repairs": 3})
    for feedback in variants:
        assert unpack_feedback(pack_feedback(feedback)) == feedback
        assert len(model.canonical(pack_feedback(feedback))) <= FEEDBACK_RESERVE
