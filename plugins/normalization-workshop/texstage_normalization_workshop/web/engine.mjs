// SPDX-License-Identifier: Apache-2.0
import {canonical,sha256} from "./identity.mjs";
import {seedFor,answerFor,parse,fields,InputError,ResourceLimit} from "./validation.mjs";
import {Theory,Budget} from "./fd.mjs";
import {chase} from "./chase.mjs";
export function analyze(exercise,submitted,budget=new Budget()) {
  exercise=seedFor(exercise); submitted=answerFor(submitted,exercise);
  const theory=new Theory(exercise,budget), mode=exercise.task.mode;
  const data={format:1,exercise:sha256(canonical(["normalization-exercise-v1",exercise])),
    answer:sha256(canonical(["normalization-answer-v1",submitted])),mode};
  if(mode==="classify") {
    const {description,keys}=theory.describe(theory.universe);
    const {relation,...facts}=description;
    data.facts={...facts,keys,witness_valid:theory.witnessValid(submitted.normal_form,submitted.witness)};
  } else {
    const parts=submitted.relations,cover=parts.reduce((a,b)=>a|b,0), covered=cover===theory.universe;
    data.facts={covered,missing:theory.universe & ~cover,
      components:parts.map(p=>theory.describe(p).description),
      preservation:covered?theory.preservation(parts):null,join:covered?chase(theory,parts):null};
  }
  if(canonical(data).length>8192) throw new ResourceLimit("data-bytes");
  return data;
}
export function start() { return {}; }
export function load(_library,raw,options={}) {
  if(!fields(options,[])) throw new InputError("options");
  return {exercise:seedFor(parse(raw)),used:false,disposed:false};
}
export function evaluate(state,text) {
  if(!state || state.used || state.disposed) throw new Error("fresh-state-required");
  state.used=true;
  if(typeof text!=="string" || text.length>4000 || [...text].length>2000) return {status:"refused"};
  try {
    const submitted=answerFor(parse(text,8000),state.exercise);
    const data=analyze(state.exercise,submitted);
    return {status:"ok",canonical:canonical(data),data,summary:{kind:"text",
      text:"Schema properties checked under the stated functional dependencies."}};
  } catch(error) {
    if(error instanceof InputError) return {status:"syntax"};
    if(error instanceof ResourceLimit) return {status:"refused"};
    throw error;
  }
}
export function dispose(state) {
  if(state) { state.disposed=true; state.exercise=null; }
}
