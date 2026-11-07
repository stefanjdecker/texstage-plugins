// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical, sha256} from "./identity.mjs";
import {answer, checkModel, clone, validateSource, DomainError, InputError, ResourceLimit, need} from "./validation.mjs";

export function compileModel(exercise, submission) {
  submission = answer(submission);
  const decisions = new Map(exercise.decisions.map(d => [d.id,d])), choices = new Map();
  for (const [key,option] of submission.choices) {
    if (!decisions.has(key)) throw new DomainError("unknown-decision",key);
    if (choices.has(key)) throw new DomainError("duplicate-decision",key);
    choices.set(key,option);
  }
  for (const key of [...decisions.keys()].sort()) {
    if (!choices.has(key)) throw new DomainError("missing-decision",key);
  }
  const model = clone(exercise.model), rel = model.relationship;
  for (const key of [...decisions.keys()].sort()) {
    const decision = decisions.get(key), option = decision.options.find(o => o.id === choices.get(key));
    if (!option) throw new DomainError("unknown-option",key);
    if (decision.kind === "role-bounds") Object.assign(rel.roles.find(r => r.id === decision.target),option.value);
    else if (decision.kind === "attribute-owner") rel.attributes.find(a => a.id === decision.target).owner = option.value;
    else Object.assign(rel,option.value);
  }
  return model;
}

export function semanticSeed(exercise) {
  return {format:exercise.format, id:exercise.id, model:exercise.model, decisions:exercise.decisions,
    requirements:exercise.requirements.map(r => r.id),
    snapshots:exercise.snapshots.map(w => Object.fromEntries(Object.entries(w).filter(([k]) => k !== "visibility")))};
}

export function firstFailure(model, world) {
  const rel = model.relationship, entities = new Map(world.entities.map(e => [e.entity,e.ids]));
  const links = world.links.map(row => ({...row, roles:new Map(row.roles), values:new Map(row.values)}));
  const issue = (code,target,occurrences) => ({code,target,occurrences});
  if (rel.pair_unique) {
    const seen = new Map();
    for (const row of links) {
      const key = canonical(rel.roles.map(role => row.roles.get(role.id)));
      if (seen.has(key)) return issue("pair-unique",rel.id,[seen.get(key),row.id]);
      seen.set(key,row.id);
    }
  }
  for (const role of rel.roles) {
    for (const entity of entities.get(role.entity)) {
      const incident = links.filter(row => row.roles.get(role.id) === entity).map(row => row.id);
      if (incident.length < role.min) return issue("role-minimum",role.id,[entity]);
      if (role.max !== "many" && incident.length > role.max) return issue("role-maximum",role.id,incident.slice(0,2));
    }
  }
  for (const attribute of rel.attributes) {
    if (attribute.owner === "relationship") continue;
    const groups = new Map();
    for (const row of links) {
      const owner = row.roles.get(attribute.owner), value = row.values.get(attribute.id);
      if (groups.has(owner) && groups.get(owner)[0] !== value)
        return issue("attribute-dependency",attribute.id,[groups.get(owner)[1],row.id]);
      if (!groups.has(owner)) groups.set(owner,[value,row.id]);
    }
  }
  return null;
}

export function source(value) {
  const exercise = validateSource(value);
  let choices = [[]];
  for (const decision of exercise.decisions) choices =
    choices.flatMap(prefix => decision.options.map(option => [...prefix,[decision.id,option.id]]));
  for (const selection of choices) checkModel(compileModel(exercise,{format:1,choices:selection}));
  for (const worked of exercise.worked_answers) {
    let model;
    try { model = compileModel(exercise,worked); } catch (error) {
      if (!(error instanceof DomainError)) throw error;
      throw new InputError("worked-answer");
    }
    need(exercise.snapshots.every(w => (firstFailure(model,w) === null) === (w.expected === "allow")),
         "worked-answer-contradicts-witness");
  }
  return exercise;
}

export function analyze(exercise, submission) {
  submission = answer(submission);
  const data = {format:1,exercise_digest:sha256(canonical(semanticSeed(exercise))),
    answer_digest:sha256(canonical(["er-answer-v1",submission])),
    model_valid:true,structural_issues:[],checks:[],unresolved:[]};
  try {
    const model = compileModel(exercise,submission);
    data.checks = exercise.snapshots.map(world => {
      const reason = firstFailure(model,world);
      return {id:world.id,expected:world.expected,admits:reason === null,reason};
    });
  } catch (error) {
    if (!(error instanceof DomainError)) throw error;
    data.model_valid = false; data.structural_issues = [error.issue];
  }
  if (canonical(data).length > 6144) throw new ResourceLimit("facts-bytes");
  return data;
}
