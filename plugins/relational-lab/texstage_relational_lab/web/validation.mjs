// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";

export const OPS = ["rel","select","project","rename","product","join","union","difference"];
export const RULES = ["split-select","push-select-left","push-select-right","product-to-join","collapse-project"];
export const CHILDREN = {rel:[], select:[1], project:[1], rename:[1], product:[1,2], join:[1,2], union:[1,2], difference:[1,2]};
export class InputError extends Error {}
export class ResourceLimit extends Error {}
export class DomainError extends Error {
  constructor(reason, node = -1) { super(reason); this.reason = reason; this.node = node; }
}
export const requireInput = condition => { if (!condition) throw new InputError("Invalid relational input"); };
export const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
export const fields = (value, names) => object(value) && Object.keys(value).length === names.length &&
  names.every(name => Object.hasOwn(value, name));
export const list = (v, lo, hi) => Array.isArray(v) && v.length >= lo && v.length <= hi;
export const id = value => typeof value === "string" && /^[a-z][a-z0-9_]{0,11}$/.test(value);
const int = (v, lo, hi) => Number.isSafeInteger(v) && v >= lo && v <= hi;
const text = (v, lo, hi) => typeof v === "string" && [...v].length >= lo && [...v].length <= hi &&
  ![...v].some(c => c.codePointAt(0) >= 0xd800 && c.codePointAt(0) <= 0xdfff);
export function scalar(value) {
  if (typeof value === "boolean") return "bool";
  if (int(value, -1000000, 1000000)) return "int";
  if (text(value, 0, 24)) return "text";
  throw new InputError("Invalid scalar");
}

// Bounded, duplicate-key rejecting JSON. The v1 format uses integer tokens only.
export function parse(textValue, byteLimit = 65536) {
  requireInput(typeof textValue === "string");
  if (new TextEncoder().encode(textValue).length > byteLimit) throw new ResourceLimit("input-bytes");
  let at = 0, count = 0;
  const bad = () => { throw new InputError("Invalid bounded JSON"); };
  const space = () => { while (/[ \t\r\n]/.test(textValue[at] || "\0")) at++; };
  const string = () => {
    if (textValue[at] !== '"') bad();
    const start = at++;
    while (at < textValue.length) {
      const c = textValue[at++];
      if (c === '"') {
        let value;
        try { value = JSON.parse(textValue.slice(start, at)); } catch { bad(); }
        if (!text(value, 0, 65536)) bad();
        return value.normalize("NFC");
      }
      if (c === "\\") at++;
    }
    bad();
  };
  const value = depth => {
    if (depth > 16 || ++count > 8192) bad();
    space();
    if (textValue[at] === '"') return string();
    if (textValue[at] === "{" || textValue[at] === "[") {
      const dict = textValue[at++] === "{", close = dict ? "}" : "]";
      const result = dict ? Object.create(null) : [];
      space();
      if (textValue[at] === close) { at++; return result; }
      while (true) {
        space();
        if (dict) {
          const key = string();
          if (Object.hasOwn(result, key)) bad();
          space(); if (textValue[at++] !== ":") bad();
          result[key] = value(depth + 1);
        } else result.push(value(depth + 1));
        space();
        if (textValue[at] === close) { at++; return result; }
        if (textValue[at++] !== ",") bad();
      }
    }
    for (const [word, result] of [["true", true], ["false", false], ["null", null]]) {
      if (textValue.startsWith(word, at)) { at += word.length; return result; }
    }
    const match = /^-?(?:0|[1-9][0-9]*)/.exec(textValue.slice(at));
    if (!match) bad();
    at += match[0].length;
    const result = Number(match[0]);
    if (!Number.isSafeInteger(result)) bad();
    return result;
  };
  const result = value(0);
  space(); if (at !== textValue.length) bad();
  return result;
}

export function header(columns, max = 12) {
  requireInput(list(columns, 1, max) && columns.every(c => list(c, 2, 2) && id(c[0]) && ["int","text","bool"].includes(c[1])));
  requireInput(new Set(columns.map(c => c[0])).size === columns.length);
  return columns.map(c => [...c]).sort((a,b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0);
}
function predicateShape(atoms) {
  requireInput(list(atoms, 1, 3));
  for (const atom of atoms) {
    requireInput(list(atom, 3, 3) && ["eq","ne","lt","le","gt","ge"].includes(atom[0]));
    for (const term of atom.slice(1)) {
      requireInput(list(term, 2, 2));
      if (term[0] === "a") requireInput(id(term[1]));
      else { requireInput(term[0] === "v"); scalar(term[1]); }
    }
  }
}
export function answerFor(value) {
  requireInput(object(value));
  if (value.mode === "construct") {
    requireInput(fields(value, ["mode","tree"]) && list(value.tree, 1, 16));
    for (const node of value.tree) {
      requireInput(Array.isArray(node) && typeof node[0] === "string" && OPS.includes(node[0]));
      const op = node[0], lengths = {rel:2, select:3, project:3, rename:3, join:4, product:3, union:3, difference:3};
      requireInput(node.length === lengths[op] && CHILDREN[op].every(p => int(node[p], 0, 15)));
      if (op === "rel") requireInput(id(node[1]));
      if (op === "select" || op === "join") predicateShape(node.at(-1));
      if (op === "project") requireInput(list(node[2], 1, 12) && node[2].every(id) && new Set(node[2]).size === node[2].length);
      if (op === "rename") requireInput(list(node[2], 1, 12) && node[2].every(pair => list(pair, 2, 2) && pair.every(id)));
    }
  } else {
    requireInput(value.mode === "rewrite" && fields(value, ["mode","steps"]) && list(value.steps, 0, 8));
    for (const step of value.steps) requireInput(fields(step, ["rule","path"]) && RULES.includes(step.rule) &&
      list(step.path, 0, 7) && step.path.every(i => int(i, 0, 1)));
  }
  if (canonical(value).length > 1800) throw new ResourceLimit("answer-bytes");
  return value;
}

export function infer(tree, schemas, allowed = OPS) {
  answerFor({mode:"construct", tree});
  const headers = [], parents = tree.map(() => 0), depths = [];
  for (const [index, node] of tree.entries()) {
    const fail = reason => { throw new DomainError(reason, index); };
    const op = node[0], children = CHILDREN[op].map(p => node[p]);
    if (!allowed.includes(op)) fail("operator-not-allowed");
    if (children.some(c => c >= index)) fail("child-index");
    children.forEach(c => parents[c]++);
    depths.push(1 + Math.max(0, ...children.map(c => depths[c])));
    if (depths[index] > 8) fail("tree-depth");
    let columns;
    if (op === "rel") {
      if (!Object.hasOwn(schemas, node[1])) fail("unknown-relation");
      columns = header(schemas[node[1]]);
    } else {
      const left = new Map(headers[children[0]]);
      if (op === "select") columns = [...left];
      else if (op === "project") {
        if (node[2].some(n => !left.has(n))) fail("unknown-attribute");
        columns = node[2].map(n => [n, left.get(n)]);
      } else if (op === "rename") {
        const names = new Map(node[2]);
        if (names.size !== node[2].length) fail("duplicate-attribute");
        if ([...names.keys()].some(n => !left.has(n))) fail("unknown-attribute");
        columns = [...left].map(([n,t]) => [names.get(n) ?? n, t]);
        if (new Set(columns.map(c => c[0])).size !== columns.length) fail("attribute-collision");
      } else {
        const right = new Map(headers[children[1]]);
        if (op === "union" || op === "difference") {
          if (canonical([...left]) !== canonical([...right])) fail("incompatible-headers");
          columns = [...left];
        } else {
          if ([...left.keys()].some(n => right.has(n))) fail("attribute-collision");
          columns = [...left, ...right];
        }
      }
      if (columns.length > 12) fail("width-limit");
      columns = header(columns);
      if (op === "select" || op === "join") {
        const types = new Map(columns);
        for (const [comparison, a, b] of node.at(-1)) {
          const kinds = [a, b].map(([kind, v]) => {
            if (kind === "v") return scalar(v);
            if (!types.has(v)) fail("unknown-attribute");
            return types.get(v);
          });
          if (kinds[0] !== kinds[1]) fail("type-mismatch");
          if (!["eq","ne"].includes(comparison) && kinds[0] !== "int") fail("unordered-type");
        }
      }
    }
    headers.push(columns);
  }
  if (parents.at(-1) !== 0 || parents.slice(0,-1).some(n => n !== 1)) throw new DomainError("not-a-tree");
  const order = [];
  const visit = i => { CHILDREN[tree[i][0]].forEach(p => visit(tree[i][p])); order.push(i); };
  visit(tree.length - 1);
  if (order.some((v,i) => v !== i)) throw new DomainError("postorder");
  return headers;
}

export function sourceFor(value) {
  requireInput(object(value) && object(value.task));
  if (new TextEncoder().encode(JSON.stringify(value)).length > 65536) throw new ResourceLimit("seed-bytes");
  const construct = value.task.mode === "construct";
  requireInput(fields(value, ["format","id","title","prompt","relations","instances","task",
    ...(construct ? ["initial_tree","reference_tree"] : ["baseline_tree"])]));
  requireInput(value.format === 1 && id(value.id));
  for (const field of ["title","prompt"]) requireInput(fields(value[field], ["en","de"]) &&
    Object.values(value[field]).every(v => text(v, 1, 600)));
  requireInput(object(value.relations) && list(Object.keys(value.relations), 1, 4) && Object.keys(value.relations).every(id));
  Object.values(value.relations).forEach(c => header(c, 6));
  requireInput(list(value.instances, 1, 4));
  const ids = new Set();
  for (const instance of value.instances) {
    requireInput(fields(instance, ["id","visibility","tables"]) && id(instance.id) && !ids.has(instance.id) &&
      ["public","private"].includes(instance.visibility));
    ids.add(instance.id);
    requireInput(fields(instance.tables, Object.keys(value.relations)));
    for (const [name, columns] of Object.entries(value.relations)) {
      requireInput(list(instance.tables[name], 0, 12));
      for (const row of instance.tables[name]) requireInput(list(row, columns.length, columns.length) &&
        row.every((v,i) => scalar(v) === columns[i][1]));
    }
  }
  requireInput(value.instances.filter(i => i.visibility === "public").length === 1);
  const task = value.task;
  requireInput(fields(task, ["mode","allowed_operators","feedback",
    ...(construct ? ["expected_header"] : ["allowed_rules","goal"])]));
  requireInput(task.feedback === "on-reveal" && list(task.allowed_operators, 1, 8) &&
    task.allowed_operators.every(op => OPS.includes(op)) && new Set(task.allowed_operators).size === task.allowed_operators.length);
  if (!construct) requireInput(task.mode === "rewrite" && task.goal === "reduce-public-materialization" &&
    list(task.allowed_rules, 1, 5) && task.allowed_rules.every(r => RULES.includes(r)) &&
    new Set(task.allowed_rules).size === task.allowed_rules.length);
  const expected = infer(construct ? value.reference_tree : value.baseline_tree, value.relations, task.allowed_operators).at(-1);
  if (construct) {
    requireInput(canonical(expected) === canonical(header(task.expected_header)));
    requireInput(list(value.initial_tree, 0, 16));
    if (value.initial_tree.length) infer(value.initial_tree, value.relations, task.allowed_operators);
  }
  return value;
}
