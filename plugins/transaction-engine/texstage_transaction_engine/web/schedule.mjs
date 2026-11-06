// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical, sha256} from "./identity.mjs";

const id = value => typeof value === "string" && /^[a-z][a-z0-9_]{0,11}$/.test(value);
const integer = (v, limit) => Number.isSafeInteger(v) && Math.abs(v) <= limit;
const object = v => v !== null && typeof v === "object" && !Array.isArray(v);
const fields = (v, names) => object(v) && Object.keys(v).length === names.length &&
  names.every(name => Object.hasOwn(v, name));
const require = condition => { if (!condition) throw new Error("Invalid transaction exercise"); };
const list = (v, min, max) => Array.isArray(v) && v.length >= min && v.length <= max;

// JSON.parse alone silently accepts duplicate keys. Keep seed and answer parsing
// unambiguous, bounded, and independent of any host/third-party parser.
function parse(text) {
  let at = 0, nodes = 0;
  const bad = () => { throw new SyntaxError("Invalid bounded JSON"); };
  const whitespace = () => { while (/[ \t\r\n]/.test(text[at] || "\0")) at++; };
  const string = () => {
    if (text[at] !== '"') bad();
    const start = at++;
    while (at < text.length) {
      const char = text[at++];
      if (char === '"') return JSON.parse(text.slice(start, at));
      if (char === "\\") at++;
    }
    bad();
  };
  const value = depth => {
    if (depth > 16 || ++nodes > 512) bad();
    whitespace();
    if (text[at] === '"') return string();
    if (text[at] === "{" || text[at] === "[") {
      const dict = text[at++] === "{", close = dict ? "}" : "]";
      const result = dict ? Object.create(null) : [];
      whitespace();
      if (text[at] === close) { at++; return result; }
      while (true) {
        whitespace();
        if (dict) {
          const key = string();
          if (Object.hasOwn(result, key)) bad();
          whitespace(); if (text[at++] !== ":") bad();
          result[key] = value(depth + 1);
        } else result.push(value(depth + 1));
        whitespace();
        if (text[at] === close) { at++; return result; }
        if (text[at++] !== ",") bad();
      }
    }
    for (const [word, result] of [["true",true],["false",false],["null",null]]) {
      if (text.startsWith(word, at)) { at += word.length; return result; }
    }
    const number = /-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(text.slice(at));
    if (!number || number.index !== 0) bad();
    at += number[0].length;
    const result = Number(number[0]);
    if (!Number.isFinite(result)) bad();
    return result;
  };
  const result = value(0);
  whitespace(); if (at !== text.length) bad();
  return result;
}

function orderReasons(model, order) {
  const reasons = [], known = new Set(model.operations.keys()), seen = new Set(order);
  if (order.some(op => !known.has(op))) reasons.push("unknown-operation");
  if (seen.size !== order.length) reasons.push("duplicate-operation");
  if ([...known].some(op => !seen.has(op))) reasons.push("missing-operation");
  if (!reasons.length && model.programs.some(program =>
    canonical(order.filter(op => program.includes(op))) !== canonical(program))) {
    reasons.push("program-order");
  }
  return reasons;
}

function modelFor(exercise) {
  require(fields(exercise, ["format","id","language","title","prompt","initial","transactions","schedule","task"]));
  require(exercise.format === 1 && id(exercise.id) && ["en","de"].includes(exercise.language));
  for (const field of ["title","prompt"]) {
    require(fields(exercise[field], ["en","de"]));
    for (const text of Object.values(exercise[field])) require(typeof text === "string" && [...text].length >= 1 && [...text].length <= 600);
  }
  require(object(exercise.initial) && Object.keys(exercise.initial).length >= 1 && Object.keys(exercise.initial).length <= 3);
  require(Object.entries(exercise.initial).every(([k,v]) => id(k) && integer(v, 1000000)));
  require(fields(exercise.task, ["repair","feedback"]) &&
    exercise.task.repair === "conflict-serializable" && exercise.task.feedback === "staged");
  require(list(exercise.transactions, 2, 3));
  const operations = new Map(), tids = new Set(), programs = [];
  let rw = 0;
  for (const transaction of exercise.transactions) {
    require(fields(transaction, ["id","operations"]) && typeof transaction.id === "string" &&
      /^T[123]$/.test(transaction.id) && !tids.has(transaction.id));
    tids.add(transaction.id);
    const program = transaction.operations, reads = new Set();
    require(list(program, 2, 13) && program.at(-1)?.kind === "commit");
    for (const [index, op] of program.entries()) {
      require(object(op) && id(op.id) && !operations.has(op.id));
      if (op.kind === "commit") {
        require(fields(op, ["id","kind"]) && index === program.length - 1);
      } else {
        require(["read","write"].includes(op.kind) && id(op.object) && Object.hasOwn(exercise.initial, op.object));
        require(fields(op, op.kind === "read" ? ["id","kind","object"] : ["id","kind","object","value"]));
        require(++rw <= 12);
        if (op.kind === "read") reads.add(op.id);
        else {
          const v = op.value;
          require(fields(v, ["constant"]) && integer(v.constant, 1000000) ||
            fields(v, ["read","add"]) && id(v.read) && reads.has(v.read) && integer(v.add, 10000));
        }
      }
      operations.set(op.id, {...op, transaction: transaction.id});
    }
    programs.push(program.map(op => op.id));
  }
  const model = {operations, programs, vertices: [...tids].sort(), initial: {...exercise.initial}};
  require(list(exercise.schedule, 4, 15) && exercise.schedule.every(id) && !orderReasons(model, exercise.schedule).length);
  // Presentation language and wording do not change analysis/grouping identity.
  model.identity = sha256(canonical({
    format: exercise.format, id: exercise.id, initial: exercise.initial,
    transactions: [...exercise.transactions].sort((a,b) => a.id < b.id ? -1 : 1),
    schedule: exercise.schedule,
  }));
  return model;
}

function certificate(vertices, edges) {
  const successors = new Map(vertices.map(v => [v, []]));
  const indegrees = new Map(vertices.map(v => [v, 0]));
  for (const edge of edges) {
    successors.get(edge.from).push(edge.to);
    indegrees.set(edge.to, indegrees.get(edge.to) + 1);
  }
  for (const children of successors.values()) children.sort();
  const serial = [], ready = vertices.filter(v => indegrees.get(v) === 0);
  while (ready.length) {
    ready.sort();
    const vertex = ready.shift(); serial.push(vertex);
    for (const child of successors.get(vertex)) {
      indegrees.set(child, indegrees.get(child) - 1);
      if (indegrees.get(child) === 0) ready.push(child);
    }
  }
  if (serial.length === vertices.length) return {acyclic: true, serial_order: serial, cycle: []};
  const color = new Map(), path = [];
  const visit = vertex => {
    color.set(vertex, 1); path.push(vertex);
    for (const child of successors.get(vertex)) {
      if (color.get(child) === 1) return [...path.slice(path.indexOf(child)), child];
      if (!color.has(child)) {
        const cycle = visit(child); if (cycle) return cycle;
      }
    }
    path.pop(); color.set(vertex, 2);
    return null;
  };
  for (const vertex of vertices) {
    if (!color.has(vertex)) {
      const cycle = visit(vertex);
      if (cycle) return {acyclic: false, serial_order: [], cycle};
    }
  }
  throw new Error("Missing conflict certificate");
}

function analyze(model, order) {
  const base = {format: "schedule-analysis-v1", exercise: model.identity, order: [...order]};
  const reasons = orderReasons(model, order);
  if (reasons.length) return {...base, valid: false, reasons};
  const values = {...model.initial}, reads = {}, trace = [], byEdge = new Map();
  for (const operation of order) {
    const op = model.operations.get(operation), step = {operation};
    if (op.kind === "read") step.value = reads[operation] = values[op.object];
    else if (op.kind === "write") {
      step.value = values[op.object] = Object.hasOwn(op.value, "constant")
        ? op.value.constant : reads[op.value.read] + op.value.add;
    }
    trace.push(step);
  }
  for (let i = 0; i < order.length; i++) {
    const a = model.operations.get(order[i]);
    for (let j = i + 1; j < order.length; j++) {
      const b = model.operations.get(order[j]);
      if (a.kind === "commit" || b.kind === "commit" || a.transaction === b.transaction ||
          a.object !== b.object || a.kind === "read" && b.kind === "read") continue;
      const name = a.transaction + ":" + b.transaction;
      if (!byEdge.has(name)) byEdge.set(name, {from: a.transaction, to: b.transaction, witnesses: []});
      byEdge.get(name).witnesses.push([a.id, b.id]);
    }
  }
  const edges = [...byEdge.keys()].sort().map(k => byEdge.get(k));
  for (const edge of edges) edge.witnesses.sort((a,b) => canonical(a) < canonical(b) ? -1 : 1);
  return {...base, valid: true, vertices: model.vertices, final: values, reads, trace, edges,
    ...certificate(model.vertices, edges)};
}

export function start() { return {}; }
export function load(_library, seed, options = {}) {
  if (typeof seed !== "string" || seed.length > 32768 || new TextEncoder().encode(seed).length > 32768 ||
      !fields(options, [])) throw new Error("Invalid transaction seed or options");
  return {model: modelFor(parse(seed)), used: false, disposed: false};
}
export function evaluate(state, text) {
  if (!state || state.used || state.disposed) throw new Error("A fresh submission state is required");
  state.used = true;
  if (typeof text !== "string" || text.length > 2000) return {status: "refused"};
  let input;
  try { input = parse(text); } catch { return {status: "syntax"}; }
  if (!fields(input, ["order"]) || !list(input.order, 0, 30) || !input.order.every(id)) return {status: "syntax"};
  const data = analyze(state.model, input.order);
  const textSummary = !data.valid ? "Invalid operation order: " + data.reasons.join(", ") + "."
    : data.acyclic ? "The conflict graph is acyclic."
      : "The conflict graph has a cycle; this schedule is not conflict serializable.";
  // All analysis fields are ASCII IDs, enums or exact integers.
  if (canonical(data).length > 8192) throw new Error("Transaction analysis exceeds its data budget");
  return {status: "ok", canonical: canonical(data), summary: {kind: "text", text: textSummary}, data};
}
export function dispose(state) {
  if (state) { state.disposed = true; state.model = null; }
}
