// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical, sha256} from "./identity.mjs";
import {sourceFor, answerFor, ResourceLimit} from "./validation.mjs";

export class Budget {
  constructor(remaining = 65536) { this.remaining = remaining; }
  charge() { if (--this.remaining < 0) throw new ResourceLimit("work-limit"); }
}
const subset = (left, right) => (left & right) === left;

export function closure(start, fds, budget = new Budget()) {
  let known = start;
  for (;;) {
    const before = known;
    for (const fd of fds) {
      budget.charge();
      if (subset(fd.lhs, known)) known |= fd.rhs;
    }
    if (before === known) return known;
  }
}

function trace(seed, start, steps, budget) {
  let known = start;
  const applied = [];
  for (const [step, fdIndex] of steps.entries()) {
    budget.charge();
    const fd = seed.fds[fdIndex];
    const kind = !subset(fd.lhs, known) ? "unmet-lhs" : subset(fd.rhs, known) ? "no-progress" : null;
    if (kind) return {reached: known, steps: applied, error: {kind, step, missing: fd.lhs & ~known}};
    applied.push([fdIndex, fd.rhs & ~known]);
    known |= fd.rhs;
  }
  return {reached: known, steps: applied, error: null};
}

export function analyze(input, submission, budget = new Budget()) {
  const seed = sourceFor(input), answer = answerFor(seed, submission), task = seed.task;
  const universe = (1 << seed.attributes.length) - 1;
  let facts;
  if (task.mode === "keys") {
    const table = Array.from({length: universe + 1}, (_, mask) => closure(mask, seed.fds, budget));
    const removable = mask => {
      let result = 0;
      for (let bit = 1; bit <= universe; bit <<= 1) {
        if ((mask & bit) && table[mask ^ bit] === universe) result |= bit;
      }
      return result;
    };
    const candidate_keys = [];
    for (let mask = 0; mask <= universe; mask++) {
      if (table[mask] === universe && removable(mask) === 0) candidate_keys.push(mask);
    }
    facts = {candidate_keys, checks: answer.keys.map(mask => [mask, table[mask], removable(mask)])};
  } else if (task.mode === "closure") {
    facts = {closure: closure(task.start, seed.fds, budget), trace: trace(seed, task.start, answer.steps, budget)};
  } else {
    const reached = closure(task.lhs, seed.fds, budget);
    let proof;
    if (answer.implied) proof = {kind: "derivation", ...trace(seed, task.lhs, answer.steps, budget)};
    else {
      const violated_fds = [];
      for (const [index, fd] of seed.fds.entries()) {
        budget.charge();
        if (subset(fd.lhs, answer.agree) && !subset(fd.rhs, answer.agree)) violated_fds.push(index);
      }
      budget.charge();
      proof = {kind: "pair", agree: answer.agree, violated_fds,
        violates_target: subset(task.lhs, answer.agree) && !subset(task.rhs, answer.agree)};
    }
    facts = {closure: reached, implied: subset(task.rhs, reached), proof};
  }
  return {format: 1, exercise: sha256(canonical(["fd-exercise-v1", seed])),
    answer: sha256(canonical(["fd-answer-v1", answer])), mode: task.mode, facts};
}
