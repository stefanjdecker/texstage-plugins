// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";
export class InputError extends Error {}
export class ResourceLimit extends Error {}
export const requireInput = (ok, reason = "invalid-input") => { if (!ok) throw new InputError(reason); };
export const fields = (v, names) => v !== null && typeof v === "object" && !Array.isArray(v) &&
  Object.keys(v).length === names.length && names.every(k => Object.hasOwn(v, k));
export const integer = (x, lo=0, hi=255) => Number.isSafeInteger(x) && x >= lo && x <= hi;
export const forms = ["1nf", "2nf", "3nf", "bcnf"];
export const id = v => typeof v === "string" && /^[A-Za-z][A-Za-z0-9_]{0,11}$/.test(v);
const list = (v, lo, hi) => Array.isArray(v) && v.length >= lo && v.length <= hi;
const text = v => typeof v === "string" && ![...v].some(c => c.codePointAt(0) >= 0xd800 && c.codePointAt(0) <= 0xdfff);

// Bounded duplicate-key-rejecting JSON, integer tokens only. Owned adaptation
// of the collection's Apache-2.0 parser; no sibling-provider imports.
export function parse(input, byteLimit=65536) {
  requireInput(typeof input === "string");
  if (new TextEncoder().encode(input).length > byteLimit) throw new ResourceLimit("input-bytes");
  let at=0, count=0;
  const bad = () => { throw new InputError("json"); };
  const space = () => { while (/[ \t\r\n]/.test(input[at] || "\0")) at++; };
  const string = () => {
    if (input[at] !== '"') bad();
    const start=at++;
    while (at < input.length) {
      const c=input[at++];
      if (c === '"') {
        let v;
        try { v=JSON.parse(input.slice(start,at)); } catch { bad(); }
        if (!text(v)) bad();
        return v.normalize("NFC");
      }
      if (c === "\\") at++;
    }
    bad();
  };
  const value = depth => {
    if (depth > 16 || ++count > 8192) throw new ResourceLimit("json-depth-or-values");
    space();
    if (input[at] === '"') return string();
    if (input[at] === "{" || input[at] === "[") {
      const dict=input[at++] === "{", close=dict ? "}" : "]";
      const result=dict ? Object.create(null) : [];
      space(); if (input[at] === close) { at++; return result; }
      while (true) {
        space();
        if (dict) {
          if (++count > 8192) throw new ResourceLimit("json-depth-or-values");
          const key=string();
          if (Object.hasOwn(result,key)) bad();
          space(); if (input[at++] !== ":") bad();
          result[key]=value(depth+1);
        } else result.push(value(depth+1));
        space();
        if (input[at] === close) { at++; return result; }
        if (input[at++] !== ",") bad();
      }
    }
    for (const [word,v] of [["true",true],["false",false],["null",null]]) {
      if (input.startsWith(word,at)) { at+=word.length; return v; }
    }
    const match=/^-?(?:0|[1-9][0-9]*)/.exec(input.slice(at));
    if (!match) bad();
    at+=match[0].length;
    const n=Number(match[0]); if (!Number.isSafeInteger(n)) bad();
    return n;
  };
  const result=value(0);
  space(); if (at !== input.length) bad();
  return result;
}
export function taskFor(v) {
  if (v?.mode === "classify") requireInput(fields(v,["mode"]));
  else requireInput(fields(v,["mode","target","preserve"]) && v.mode === "decompose" &&
    ["3nf","bcnf"].includes(v.target) && typeof v.preserve === "boolean");
  return {...v};
}
export function seedFor(v) {
  requireInput(fields(v,["format","id","attributes","fds","task"]) && v.format === 1 &&
    typeof v.id === "string" && /^[A-Za-z][A-Za-z0-9_]{0,47}$/.test(v.id));
  requireInput(list(v.attributes,1,8) && v.attributes.every(id) && new Set(v.attributes).size === v.attributes.length);
  const universe=(1 << v.attributes.length)-1;
  requireInput(list(v.fds,0,32));
  let previous=-1;
  for (const fd of v.fds) {
    requireInput(list(fd,2,2) && integer(fd[0],0,universe) && integer(fd[1],1,universe) &&
      !(fd[1] & (fd[1]-1)) && !(fd[0] & fd[1]),"fd");
    const key=fd[0]*256+fd[1];
    requireInput(key > previous,"noncanonical-fds"); previous=key;
  }
  taskFor(v.task);
  return {format:1,id:v.id,attributes:[...v.attributes],fds:v.fds.map(x=>[...x]),task:{...v.task}};
}
export function answerFor(v,exercise) {
  requireInput(v?.mode === exercise.task.mode,"mode");
  const universe=(1 << exercise.attributes.length)-1;
  let result;
  if (v.mode === "classify") {
    requireInput(fields(v,["mode","normal_form","witness"]) && forms.includes(v.normal_form));
    const w=v.witness;
    requireInput(w === null || (list(w,2,2) && integer(w[0],0,universe) &&
      integer(w[1],1,universe) && !(w[1] & (w[1]-1))),"witness");
    result={...v,witness:w === null ? null : [...w]};
  } else {
    requireInput(fields(v,["mode","relations"]) && list(v.relations,1,8) &&
      v.relations.every(x=>integer(x,1,universe)) && new Set(v.relations).size === v.relations.length,"relations");
    result={mode:v.mode,relations:[...v.relations].sort((a,b)=>a-b)};
  }
  if (canonical(result).length > 512) throw new ResourceLimit("answer-bytes");
  return result;
}
