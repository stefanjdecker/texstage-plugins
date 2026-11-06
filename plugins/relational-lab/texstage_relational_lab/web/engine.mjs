// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical, sha256} from "./identity.mjs";
import {answerFor, fields, parse, sourceFor, InputError, DomainError, ResourceLimit} from "./validation.mjs";
import {Budget, evaluateTree, exerciseIdentity, relationFacts} from "./algebra.mjs";
import {rewriteTree} from "./rewrites.mjs";

export function analyze(exercise, submission, budget = new Budget()) {
  answerFor(submission);
  const base = {format:"relational-analysis-v1", exercise:exerciseIdentity(exercise),
    answer:sha256(canonical(["relational-answer-v1",submission])), mode:exercise.task.mode};
  let stepIndex = -1;
  try {
    if (submission.mode !== base.mode) throw new DomainError("wrong-mode");
    let tree = submission.tree ?? exercise.baseline_tree;
    const sequence = [tree];
    if (base.mode === "rewrite") for (const [index, step] of submission.steps.entries()) {
      stepIndex = index;
      tree = rewriteTree(exercise, tree, step);
      sequence.push(tree);
    }
    let fixtures, publicStats, baselineCells;
    for (const [index, current] of sequence.entries()) {
      fixtures = [];
      for (const instance of [...exercise.instances].sort((a,b) => a.id < b.id ? -1 : 1)) {
        const result = evaluateTree(exercise, current, instance, budget);
        fixtures.push(relationFacts(result.relation, instance.id));
        if (instance.visibility === "public") publicStats = result.stats;
      }
      if (index === 0) baselineCells = publicStats.cells;
    }
    const result = {...base, valid:true, fixtures, public:publicStats};
    if (base.mode === "rewrite") result.proof = {verified:true, steps:submission.steps.length, tree,
      baseline_cells:baselineCells, improved:publicStats.cells < baselineCells};
    return result;
  } catch (error) {
    if (!(error instanceof DomainError)) throw error;
    return {...base, valid:false, reason:error.reason, node:error.node, step:stepIndex};
  }
}
export function start() { return {}; }
export function load(_library, seed, options = {}) {
  if (!fields(options, [])) throw new InputError("Options must be empty");
  return {exercise:sourceFor(parse(seed)), used:false, disposed:false};
}
export function evaluate(state, text) {
  if (!state || state.used || state.disposed) throw new Error("A fresh submission state is required");
  state.used = true;
  if (typeof text !== "string" || text.length > 2000) return {status:"refused"};
  let data;
  try {
    const submission = answerFor(parse(text, 8000));
    data = analyze(state.exercise, submission);
    if (canonical(data).length > 8192) throw new ResourceLimit("data-bytes");
  } catch (error) {
    if (error instanceof InputError) return {status:"syntax"};
    if (error instanceof ResourceLimit) return {status:"refused"};
    throw error;
  }
  const summary = !data.valid ? "Invalid query or rewrite: " + data.reason + "." :
    data.mode === "rewrite" ? "The rewrite certificate is verified; this is not a runtime cost estimate." :
      "Query evaluated on the exercise instances. Matching results is not proof of equivalence.";
  return {status:"ok", canonical:canonical(data), summary:{kind:"text", text:summary}, data};
}
export function dispose(state) {
  if (state) { state.disposed = true; state.exercise = null; }
}
