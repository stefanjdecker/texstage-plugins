// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import exerciseSchema from "../schemas/exercise-v1.json" with {type: "json"};
import answerSchema from "../schemas/answer-v1.json" with {type: "json"};
import modelSchema from "../schemas/model-v1.json" with {type: "json"};
import {canonical} from "./identity.mjs";

export class InputError extends Error {}
export class ResourceLimit extends Error {}
export class DomainError extends Error {
  constructor(code, target) { super(code); this.issue = {code, target, occurrences: []}; }
}
export const need = (condition, code = "invalid-source") => { if (!condition) throw new InputError(code); };
export const id = value => typeof value === "string" && value.length >= 1 && value.length <= 24 &&
  !/[^A-Za-z0-9_-]/.test(value);
export const cmp = (a,b) => a < b ? -1 : a > b ? 1 : 0;
export const byId = (a,b) => cmp(a.id,b.id);
export const pairsOrder = (a,b) => cmp(a[0],b[0]) || cmp(a[1],b[1]);
export const clone = value => JSON.parse(JSON.stringify(value));
export const ids = values => need(values.every(id) && new Set(values).size === values.length, "ids");
export const object = value => value !== null && typeof value === "object" && !Array.isArray(value);

// Small non-executable interpreter for the *owned frozen schemas*.
// It is not a replacement for the host's independent result validators.
function accepts(schema, value, root = schema) {
  if (schema === true) return true;
  if (schema === false) return false;
  if (schema.$ref) return accepts(root.$defs[schema.$ref.split("/").at(-1)], value, root);
  if (schema.oneOf && schema.oneOf.filter(s => accepts(s,value,root)).length !== 1) return false;
  if (Object.hasOwn(schema,"const") && value !== schema.const) return false;
  if (schema.enum && !schema.enum.some(v => v === value)) return false;
  if (schema.type) {
    const valid = {
      object: object(value), array: Array.isArray(value), null: value === null,
      string: typeof value === "string", boolean: typeof value === "boolean",
      integer: Number.isSafeInteger(value)
    };
    if (!valid[schema.type]) return false;
  }
  if (typeof value === "string") {
    const n = [...value].length;
    if (n < (schema.minLength ?? 0) || n > (schema.maxLength ?? Infinity)) return false;
  }
  if (typeof value === "number" &&
      (value < (schema.minimum ?? -Infinity) || value > (schema.maximum ?? Infinity))) return false;
  if (Array.isArray(value)) {
    if (value.length < (schema.minItems ?? 0) || value.length > (schema.maxItems ?? Infinity)) return false;
    if (schema.uniqueItems && new Set(value.map(canonical)).size !== value.length) return false;
    for (let i=0;i<value.length;i++) {
      const sub = i < (schema.prefixItems?.length ?? 0) ? schema.prefixItems[i] : (schema.items ?? true);
      if (!accepts(sub,value[i],root)) return false;
    }
  }
  if (object(value)) {
    if (schema.required?.some(k => !Object.hasOwn(value,k))) return false;
    for (const key of Object.keys(value)) {
      if (Object.hasOwn(schema.properties ?? {},key)) {
        if (!accepts(schema.properties[key],value[key],root)) return false;
      } else if (schema.additionalProperties === false) return false;
    }
  }
  return true;
}
export function shape(name, value) {
  need(accepts({exercise:exerciseSchema,answer:answerSchema,model:modelSchema}[name],value), name+"-shape");
}

const scalarString = value => typeof value === "string" &&
  ![...value].some(c => c.codePointAt(0) >= 0xd800 && c.codePointAt(0) <= 0xdfff);

// Duplicate-key rejecting, depth/work bounded JSON; integers use integer tokens.
export function parse(text, byteLimit = 65536) {
  need(scalarString(text), "json-text");
  if (new TextEncoder().encode(text).length > byteLimit) throw new ResourceLimit("input-bytes");
  let at = 0, visits = 0;
  const bad = () => { throw new InputError("json-syntax"); };
  const space = () => { while (" \t\r\n".includes(text[at] ?? "\0")) at++; };
  const string = () => {
    if (text[at] !== '"') bad();
    const start = at++;
    while (at < text.length) {
      const c = text[at++];
      if (c === '"') {
        let result;
        try { result = JSON.parse(text.slice(start,at)); } catch { bad(); }
        if (!scalarString(result)) bad();
        return result.normalize("NFC");
      }
      if (c === "\\") at++;
    }
    bad();
  };
  const value = depth => {
    if (depth > 16 || ++visits > 8192) bad();
    space();
    if (text[at] === '"') return string();
    if (text[at] === "{" || text[at] === "[") {
      const dict = text[at++] === "{", close = dict ? "}" : "]";
      const result = dict ? Object.create(null) : [];
      space();
      if (text[at] === close) { at++; return result; }
      while (true) {
        space();
        if (dict) {
          const key = string();
          if (Object.hasOwn(result,key)) bad();
          space(); if (text[at++] !== ":") bad();
          result[key] = value(depth+1);
        } else result.push(value(depth+1));
        space();
        if (text[at] === close) { at++; return result; }
        if (text[at++] !== ",") bad();
      }
    }
    for (const [word,result] of [["true",true],["false",false],["null",null]]) {
      if (text.startsWith(word,at)) { at += word.length; return result; }
    }
    const match = /^-?(?:0|[1-9][0-9]*)/.exec(text.slice(at));
    if (!match) bad();
    at += match[0].length;
    const result = Number(match[0]);
    if (!Number.isSafeInteger(result)) bad();
    return result;
  };
  const result = value(0);
  space(); if (at !== text.length) bad();
  return result;
}

export function answer(value) {
  shape("answer",value);
  need(value.choices.every(pair => pair.every(id)), "choice-id");
  if (canonical(value).length > 1024) throw new ResourceLimit("answer-bytes");
  return {...value, choices: value.choices.map(p => [...p]).sort(pairsOrder)};
}

export function checkModel(model) {
  shape("model",model);
  ids(model.entities);
  const rel = model.relationship, roles = rel.roles.map(r => r.id);
  need(id(rel.id) && !model.entities.includes(rel.id), "relationship-id");
  ids(roles);
  need(!roles.includes("relationship"), "reserved-role");
  need(new Set(rel.roles.map(r => r.entity)).size === 2 &&
    rel.roles.every(r => model.entities.includes(r.entity)), "role-entities");
  ids(rel.attributes.map(a => a.id));
  need(rel.attributes.every(a => roles.includes(a.owner) || a.owner === "relationship"), "attribute-owner");
  need(rel.form !== "relationship" || rel.pair_unique, "relationship-identity");
  return model;
}

export function validateSource(value) {
  shape("exercise",value);
  if (canonical(value).length > 65536) throw new ResourceLimit("seed-bytes");
  need(id(value.id), "exercise-id");
  checkModel(value.model);
  const source = clone(value), rel = source.model.relationship;
  source.model.entities.sort();
  rel.roles.sort(byId); rel.attributes.sort(byId);
  ids(source.requirements.map(r => r.id));
  ids(source.decisions.map(d => d.id));
  ids(source.snapshots.map(w => w.id));
  const requirementIds = new Set(source.requirements.map(r => r.id));
  const roleIds = rel.roles.map(r => r.id), attributes = new Map(rel.attributes.map(a => [a.id,a]));
  const used = new Set();
  for (const decision of source.decisions) {
    ids(decision.options.map(o => o.id));
    const key = canonical([decision.kind,decision.target]);
    need(id(decision.target) && !used.has(key), "slot-ownership"); used.add(key);
    if (decision.kind === "role-bounds") need(roleIds.includes(decision.target), "role-target");
    else if (decision.kind === "attribute-owner") need(attributes.has(decision.target), "attribute-target");
    else need(decision.target === rel.id, "relationship-target");
    const meanings = new Set();
    for (const option of decision.options) {
      const payload = option.value;
      if (decision.kind === "attribute-owner") need(roleIds.includes(payload) || payload === "relationship", "owner-option");
      else if (decision.kind === "relationship-form") need(payload.form !== "relationship" || payload.pair_unique, "form-option");
      const meaning = canonical(payload);
      need(!meanings.has(meaning), "duplicate-option-meaning"); meanings.add(meaning);
    }
    decision.options.sort(byId);
  }
  source.decisions.sort(byId); source.requirements.sort(byId); source.snapshots.sort(byId);
  need(source.snapshots.some(w => w.visibility === "public"), "public-example");
  for (const world of source.snapshots) {
    need(world.requirements.every(id => requirementIds.has(id)), "witness-requirements");
    world.requirements.sort();
    ids(world.entities.map(e => e.entity));
    need(world.entities.every(e => source.model.entities.includes(e.entity)), "snapshot-entities");
    const entitySets = new Map();
    let count = world.links.length;
    for (const entity of world.entities) {
      ids(entity.ids); entity.ids.sort(); count += entity.ids.length;
      entitySets.set(entity.entity,new Set(entity.ids));
    }
    need(count <= 32, "snapshot-occurrences");
    ids(world.links.map(row => row.id));
    world.entities.sort((a,b) => cmp(a.entity,b.entity)); world.links.sort(byId);
    for (const row of world.links) {
      ids(row.roles.map(p => p[0])); ids(row.values.map(p => p[0]));
      const roles = new Map(row.roles), values = new Map(row.values);
      need(roleIds.every(r => roles.has(r)) && values.size === attributes.size &&
           [...values.keys()].every(a => attributes.has(a)), "observation-fields");
      for (const role of rel.roles) need(entitySets.get(role.entity).has(roles.get(role.id)), "dangling-observation");
      for (const [key, scalar] of row.values) {
        const kind = attributes.get(key).type;
        need(kind === "int" ? Number.isInteger(scalar) : typeof scalar === (kind === "bool" ? "boolean" : "string"),
             "attribute-type");
      }
      row.roles.sort(pairsOrder); row.values.sort(pairsOrder);
    }
  }
  source.worked_answers = source.worked_answers.map(answer).sort((a,b) => cmp(canonical(a),canonical(b)));
  need(new Set(source.worked_answers.map(canonical)).size === source.worked_answers.length, "duplicate-worked");
  return source;
}
