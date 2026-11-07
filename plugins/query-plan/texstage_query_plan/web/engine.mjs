// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";
import {parse} from "./parser.mjs";
import {fields,sourceFor,InputError,ResourceLimit} from "./validation.mjs";
import {analyze} from "./model.mjs";
export function start() { return {}; }
export function load(_library, seed, options = {}) {
  if (!fields(options,[])) throw new InputError("Options must be empty");
  return {exercise:sourceFor(parse(seed)),used:false,disposed:false};
}
export function evaluate(state, text) {
  if (!state || state.used || state.disposed) throw new Error("Fresh submission state required");
  state.used = true;
  if (typeof text !== "string" || text.length > 2000) return {status:"refused"};
  try {
    const data = analyze(state.exercise,parse(text,2000));
    const summary = data.valid ? "Estimated teaching cost: " + data.cost + ". Not execution time." :
      "Plan is not feasible: " + data.reason + ".";
    return {status:"ok",canonical:canonical(data),summary:{kind:"text",text:summary},data};
  } catch (error) {
    if (error instanceof InputError) return {status:"syntax"};
    if (error instanceof ResourceLimit) return {status:"refused"};
    throw error;
  }
}
export function dispose(state) {
  if (state) { state.disposed = true; state.exercise = null; }
}
