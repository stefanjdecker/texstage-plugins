// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical, sha256} from "./identity.mjs";
import {parse, InputError, ResourceLimit, object, need} from "./validation.mjs";
import {source, analyze} from "./model.mjs";

export function start() { return {}; }
export function load(_library, seed, options = {}) {
  need(object(options) && Object.keys(options).length === 0, "options");
  return {exercise:source(parse(seed)), used:false, disposed:false};
}
export function evaluate(state, text) {
  if (!state || state.used || state.disposed) throw new Error("A fresh submission state is required");
  state.used = true;
  try {
    const data = analyze(state.exercise,parse(text,1024));
    const result = {status:"ok", canonical:"er-decisions-v1:" + sha256(canonical(data)),
      summary:{kind:"text",text: data.model_valid
        ? "Model checked against finite examples; this is not a proof of ER equivalence."
        : "The decision set is invalid; no snapshot findings were fabricated."},data};
    if (canonical(result).length > 10240) throw new ResourceLimit("outcome-bytes");
    return result;
  } catch (error) {
    if (error instanceof InputError) return {status:"syntax"};
    if (error instanceof ResourceLimit) return {status:"refused"};
    throw error;
  }
}
export function dispose(state) {
  if (state) { state.disposed = true; state.exercise = null; }
}
