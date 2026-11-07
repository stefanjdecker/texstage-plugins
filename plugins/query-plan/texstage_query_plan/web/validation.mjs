// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";
export class InputError extends Error {}
export class ResourceLimit extends Error {}
export class DomainError extends Error {
  constructor(reason, node = -1) { super(reason); this.reason = reason; this.node = node; }
}
export const requireInput = ok => { if (!ok) throw new InputError("Invalid query-plan input"); };
export const object = v => v !== null && typeof v === "object" && !Array.isArray(v) &&
  [null, Object.prototype].includes(Object.getPrototypeOf(v));
export const fields = (v, required, optional = []) => object(v) &&
  required.every(k => Object.hasOwn(v,k)) && Object.keys(v).every(k => [...required,...optional].includes(k));
export const text = (v, lo, hi) => typeof v === "string" && [...v].length >= lo && [...v].length <= hi &&
  ![...v].some(c => c.codePointAt(0) >= 0xd800 && c.codePointAt(0) <= 0xdfff);
const id = v => typeof v === "string" && /^[a-z][a-z0-9_]{0,15}(?![\s\S])/.test(v);
const int = (v, lo, hi) => Number.isSafeInteger(v) && v >= lo && v <= hi;
const array = (v, lo, hi) => Array.isArray(v) && v.length >= lo && v.length <= hi;
export function budget(value, limit) {
  let count = 0;
  const visit = (v, depth) => {
    requireInput(++count <= 2048 && depth <= 16);
    if (Array.isArray(v)) v.forEach(x => visit(x,depth+1));
    else if (object(v)) {
      for (const [k, x] of Object.entries(v)) { requireInput(text(k,0,98304)); visit(x,depth+1); }
    } else requireInput(v === null || typeof v === "boolean" ||
      int(v,-Number.MAX_SAFE_INTEGER,Number.MAX_SAFE_INTEGER) || text(v,0,98304));
  };
  visit(value,0);
  if (canonical(value).length > limit) throw new ResourceLimit("canonical-bytes");
}
function connected(mask, edges) {
  let reached = mask & -mask;
  while (true) {
    const old = reached;
    for (const edge of edges) if ((edge & mask) === edge && (edge & reached)) reached |= edge;
    if (reached === old) return mask !== 0 && reached === mask;
  }
}
export function sourceFor(value) {
  budget(value,32768);
  requireInput(fields(value,["format","model","query","statistics","limits"]) &&
    value.format === 1 && value.model === "teaching-cost-v1");
  const q = value.query;
  requireInput(fields(q,["relations","joins","output"]) && array(q.relations,1,3));
  const relations = new Map();
  for (const r of q.relations) {
    requireInput(fields(r,["id","columns"],["filter","index"]) && id(r.id) &&
      !relations.has(r.id) && array(r.columns,1,8));
    const columns = new Map();
    for (const c of r.columns) {
      requireInput(fields(c,["id","type"]) && id(c.id) && !columns.has(c.id) &&
        ["int","text","bool"].includes(c.type));
      columns.set(c.id,c.type);
    }
    if (Object.hasOwn(r,"filter")) {
      const f = r.filter;
      requireInput(fields(f,["column","value"]) && id(f.column) && columns.has(f.column));
      const t = columns.get(f.column), v = f.value;
      requireInput((t === "int" && int(v,-1000000,1000000)) ||
        (t === "bool" && typeof v === "boolean") ||
        (t === "text" && text(v,0,64) && v.normalize("NFC") === v));
    }
    if (Object.hasOwn(r,"index")) requireInput(fields(r.index,["column","height"]) &&
      Object.hasOwn(r,"filter") && id(r.index.column) &&
      r.index.column === r.filter.column && int(r.index.height,1,8));
    relations.set(r.id,columns);
  }
  const names = [...relations.keys()].sort(), bits = new Map(names.map((n,i) => [n,1<<i]));
  const ref = r => {
    requireInput(array(r,2,2) && r.every(id) && relations.has(r[0]) && relations.get(r[0]).has(r[1]));
    return relations.get(r[0]).get(r[1]);
  };
  requireInput(array(q.joins,names.length-1,names.length-1));
  const edges = [], joins = [];
  for (const j of q.joins) {
    requireInput(fields(j,["left","right"]) && ref(j.left) === ref(j.right) && j.left[0] !== j.right[0]);
    const edge = bits.get(j.left[0]) | bits.get(j.right[0]);
    requireInput(!edges.includes(edge)); edges.push(edge);
    const [left,right] = [j.left,j.right].sort((a,b) => canonical(a) < canonical(b) ? -1 : 1);
    joins.push({left,right});
  }
  requireInput(connected((1<<names.length)-1,edges) && array(q.output,1,8));
  q.output.forEach(ref);
  const stats = value.statistics;
  requireInput(fields(stats,["base","cardinalities"]) && array(stats.base,names.length,names.length));
  const base = new Map();
  for (const b of stats.base) {
    requireInput(fields(b,["relation","rows","pages","row_bytes"]) && id(b.relation) &&
      bits.has(b.relation) && !base.has(b.relation) && int(b.rows,0,1000000) &&
      int(b.pages,0,1000000) && int(b.row_bytes,1,1024) && (b.rows === 0 || b.pages > 0));
    base.set(b.relation,b);
  }
  requireInput(array(stats.cardinalities,1,7));
  const cards = new Map();
  for (const c of stats.cardinalities) {
    requireInput(fields(c,["relations","rows"]) && array(c.relations,1,3) &&
      c.relations.every(n => id(n) && bits.has(n)) &&
      new Set(c.relations).size === c.relations.length && int(c.rows,0,1000000));
    const mask = c.relations.reduce((m,n) => m | bits.get(n),0);
    requireInput(!cards.has(mask)); cards.set(mask,c.rows);
  }
  for (let mask=1; mask<(1<<names.length); mask++) {
    requireInput(cards.has(mask) === connected(mask,edges));
    if (!cards.has(mask)) continue;
    const rows = cards.get(mask);
    if ((mask & (mask-1)) === 0) {
      const name = names.find(n => bits.get(n) === mask);
      requireInput(rows <= base.get(name).rows &&
        (Object.hasOwn(q.relations.find(r => r.id === name),"filter") || rows === base.get(name).rows));
    } else {
      for (const [left,lrows] of cards) {
        const right = mask ^ left;
        if ((left & mask) === left && left !== mask && cards.has(right))
          requireInput(rows <= lrows * cards.get(right));
      }
    }
  }
  requireInput(fields(value.limits,["hash_bytes"]) && int(value.limits.hash_bytes,0,16777216));
  const normalized = JSON.parse(canonical(value));
  normalized.query.relations.sort((a,b) => a.id < b.id ? -1 : 1);
  normalized.query.relations.forEach(r => r.columns.sort((a,b) => a.id < b.id ? -1 : 1));
  normalized.query.joins = JSON.parse(canonical(joins.sort((a,b) => canonical(a) < canonical(b) ? -1 : 1)));
  normalized.statistics.base = names.map(n => JSON.parse(canonical(base.get(n))));
  normalized.statistics.cardinalities = [...cards.keys()].sort((a,b) => a-b).map(mask => ({
    relations:names.filter(n => bits.get(n) & mask),rows:cards.get(mask)
  }));
  return normalized;
}
export function answerFor(value) {
  budget(value,1024);
  requireInput(fields(value,["format","nodes"]) && value.format === 1 && array(value.nodes,1,5));
  for (const n of value.nodes) {
    requireInput(object(n));
    if (n.op === "scan") requireInput(fields(n,["op","relation","method"]) && id(n.relation) &&
      ["seq","index"].includes(n.method));
    else if (n.op === "join") requireInput(fields(n,["op","left","right","method"]) &&
      int(n.left,0,3) && int(n.right,0,3) && ["nested","hash-left","hash-right"].includes(n.method));
    else throw new InputError("Unknown operator");
  }
  return JSON.parse(canonical(value));
}
