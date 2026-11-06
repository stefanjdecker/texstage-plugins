// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical, sha256} from "./identity.mjs";
import {header, infer, ResourceLimit} from "./validation.mjs";

export class Budget {
  constructor(limit = 100000) { this.remaining = limit; }
  charge(amount = 1) {
    this.remaining -= amount;
    if (this.remaining < 0) throw new ResourceLimit("work-limit");
  }
}
// Text order is Unicode scalar order, not JS UTF-16 or locale order.
function compare(a, b) {
  if (typeof a !== "string") return a === b ? 0 : a < b ? -1 : 1;
  const x = [...a].map(c => c.codePointAt(0)), y = [...b].map(c => c.codePointAt(0));
  for (let i = 0; i < Math.min(x.length, y.length); i++) if (x[i] !== y[i]) return x[i] < y[i] ? -1 : 1;
  return Math.sign(x.length - y.length);
}
function compareRows(a, b) {
  for (let i = 0; i < a.length; i++) { const c = compare(a[i], b[i]); if (c) return c; }
  return 0;
}
export function relation(columns, inputRows) {
  const sorted = header(columns), indices = sorted.map(([n]) => columns.findIndex(c => c[0] === n));
  const unique = new Map();
  for (const input of inputRows) {
    const row = indices.map(i => input[i]);
    unique.set(canonical(row), row);
    if (unique.size > 256) throw new ResourceLimit("row-limit");
  }
  return {header: sorted, rows: [...unique.values()].sort(compareRows)};
}
export function baseRelation(exercise, instance, name) {
  return relation(exercise.relations[name], instance.tables[name]);
}
export function relationFacts(value, id) {
  return {id, header: sha256(canonical(["header-v1", value.header])),
    relation: sha256(canonical(["relation-v1", value.header, value.rows]))};
}
export function exerciseIdentity(exercise) {
  const relations = Object.fromEntries(Object.entries(exercise.relations).map(([n,c]) => [n,header(c)]));
  const instances = [...exercise.instances].sort((a,b) => a.id < b.id ? -1 : 1).map(i => ({
    id:i.id, visibility:i.visibility,
    tables:Object.fromEntries(Object.keys(relations).map(n => [n,baseRelation(exercise,i,n).rows])),
  }));
  const task = {...exercise.task};
  delete task.feedback;
  task.allowed_operators = [...task.allowed_operators].sort();
  if (task.allowed_rules) task.allowed_rules = [...task.allowed_rules].sort();
  if (task.expected_header) task.expected_header = header(task.expected_header);
  const policy = Object.fromEntries(["reference_tree","baseline_tree"].filter(k => Object.hasOwn(exercise,k)).map(k => [k,exercise[k]]));
  return sha256(canonical(["relational-exercise-v1", {id:exercise.id, relations, instances, task, ...policy}]));
}
function condition(atoms, columns, budget) {
  const names = columns.map(c => c[0]);
  const prepared = atoms.map(([op,a,b]) => [op, ...[a,b].map(term =>
    term[0] === "a" ? row => row[names.indexOf(term[1])] : () => term[1])]);
  return row => {
    for (const [op,a,b] of prepared) {
      budget.charge();
      const x = a(row), y = b(row);
      const passed = op === "eq" ? x === y : op === "ne" ? x !== y : op === "lt" ? x < y :
        op === "le" ? x <= y : op === "gt" ? x > y : x >= y;
      if (!passed) return false;
    }
    return true;
  };
}
export function evaluateTree(exercise, tree, instance, budget = new Budget()) {
  const headers = infer(tree, exercise.relations, exercise.task.allowed_operators);
  const results = [], trace = [];
  let cells = 0;
  for (const [index,node] of tree.entries()) {
    const op = node[0], outputHeader = headers[index];
    let result;
    if (op === "rel") {
      budget.charge(instance.tables[node[1]].length);
      result = baseRelation(exercise, instance, node[1]);
    } else {
      const left = results[node[1]], unique = new Map();
      const add = row => {
        unique.set(canonical(row), row);
        if (unique.size > 256) throw new ResourceLimit("row-limit");
      };
      budget.charge(left.rows.length);
      if (op === "select") {
        const test = condition(node[2], left.header, budget);
        for (const row of left.rows) if (test(row)) add(row);
      } else if (op === "project" || op === "rename") {
        const mapping = new Map(op === "rename" ? node[2] : []);
        const names = left.header.map(c => mapping.get(c[0]) ?? c[0]);
        const indices = outputHeader.map(c => names.indexOf(c[0]));
        for (const row of left.rows) add(indices.map(i => row[i]));
      } else {
        const right = results[node[2]];
        budget.charge(right.rows.length);
        if (op === "union" || op === "difference") {
          const other = new Set(right.rows.map(canonical));
          for (const row of left.rows) if (op === "union" || !other.has(canonical(row))) add(row);
          if (op === "union") right.rows.forEach(add);
        } else {
          const joinedHeader = [...left.header, ...right.header];
          const indices = outputHeader.map(c => joinedHeader.findIndex(k => k[0] === c[0]));
          const test = op === "join" ? condition(node[3], outputHeader, budget) : () => true;
          for (const a of left.rows) for (const b of right.rows) {
            budget.charge();
            const joined = [...a,...b], row = indices.map(i => joined[i]);
            if (test(row)) add(row);
          }
        }
      }
      result = {header:outputHeader, rows:[...unique.values()].sort(compareRows)};
      cells += result.rows.length * outputHeader.length;
    }
    results.push(result);
    trace.push([index, result.rows.length, result.header.length]);
  }
  return {relation:results.at(-1), stats:{trace,cells}};
}
