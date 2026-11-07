// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";
import {InputError, ResourceLimit, fields, parse, sourceFor, answerFor} from "./validation.mjs";
import {inspectTree} from "./tree.mjs";
import {analyze, Budget} from "./operations.mjs";
export {analyze, Budget};

export function start() { return {}; }
export function load(_library, seed, options = {}) {
  if (!fields(options, [])) throw new InputError("Options must be empty");
  const parsed = sourceFor(parse(seed)), budget = new Budget();
  inspectTree(parsed.tree, parsed, budget);
  return {seed: parsed, budget, used: false, disposed: false};
}
export function evaluate(state, text) {
  if (!state || state.used || state.disposed) throw new Error("A fresh submission state is required");
  state.used = true;
  if (typeof text !== "string" || text.length > 2000) return {status: "refused"};
  try {
    const answer = answerFor(state.seed, parse(text, 8000));
    const data = analyze(state.seed, answer, state.budget);
    if (canonical(data).length > 6144) throw new ResourceLimit("data-bytes");
    const result = {status: "ok", canonical: "bplus-v1:" + data.exercise + ":" + data.answer,
      summary: {kind: "text", text: "B+ tree operation analyzed; facts are not a grade."}, data};
    if (canonical(result).length > 8192) throw new ResourceLimit("result-bytes");
    return result;
  } catch (error) {
    if (error instanceof InputError) return {status: "syntax"};
    if (error instanceof ResourceLimit) return {status: "refused"};
    throw error;
  }
}
export function dispose(state) {
  if (state) { state.disposed = true; state.seed = null; state.budget = null; }
}
