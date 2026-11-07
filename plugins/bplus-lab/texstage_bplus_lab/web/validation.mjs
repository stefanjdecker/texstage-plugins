// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";

export class InputError extends Error {}
export class ResourceLimit extends Error {}
export const requireInput = condition => { if (!condition) throw new InputError("Invalid B+ input"); };
export const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
export const fields = (value, names) => object(value) && Object.keys(value).length === names.length &&
  names.every(name => Object.hasOwn(value, name));
export const list = (v, lo, hi) => Array.isArray(v) && v.length >= lo && v.length <= hi;
export const int = (v, lo, hi) => Number.isSafeInteger(v) && v >= lo && v <= hi;
const text = (v, lo, hi) => typeof v === "string" && [...v].length >= lo && [...v].length <= hi &&
  ![...v].some(c => c.codePointAt(0) >= 0xd800 && c.codePointAt(0) <= 0xdfff);
// Bounded, duplicate-key rejecting JSON. The v1 format uses integer tokens only.
export function parse(textValue, byteLimit = 32768) {
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
        return value;
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

export function sourceFor(value) {
  requireInput(fields(value, ["format", "semantics", "leaf_capacity", "internal_capacity", "tree", "task"]));
  requireInput(value.format === 1 && value.semantics === "bplus-operations-v1");
  requireInput(int(value.leaf_capacity, 3, 6) && int(value.internal_capacity, 3, 6));
  const task = value.task;
  requireInput(object(task));
  if (task.kind === "range") {
    requireInput(fields(task, ["kind", "lower", "upper"]) && int(task.lower, -9999, 9999) &&
      int(task.upper, -9999, 9999) && task.lower <= task.upper);
  } else {
    requireInput(fields(task, ["kind", "key"]) && ["lookup", "insert", "delete"].includes(task.kind) &&
      int(task.key, -9999, 9999));
  }
  if (canonical(value).length > 12288) throw new ResourceLimit("seed-bytes");
  return value;
}

export function answerFor(seed, value) {
  const kind = seed.task.kind;
  const updating = kind === "insert" || kind === "delete";
  const names = updating ? ["format", "path", "repairs", "separators", "height"] :
    kind === "range" ? ["format", "path", "keys", "leaves"] : ["format", "path", "keys"];
  requireInput(fields(value, names) && value.format === 1);
  requireInput(list(value.path, 1, 3) && value.path.every(n => int(n, 0, 63)));
  if (!updating) {
    requireInput(list(value.keys, 0, kind === "lookup" ? 1 : 40) && value.keys.every(k => int(k, -9999, 9999)));
    if (kind === "range") requireInput(list(value.leaves, 1, 20) && value.leaves.every(n => int(n, 0, 63)));
  } else {
    requireInput(int(value.height, 0, 3) && list(value.repairs, 0, 3) && list(value.separators, 0, 10));
    requireInput(value.separators.every(s => fields(s, ["node", "keys"]) && int(s.node, 0, 63) &&
      list(s.keys, 1, 5) && s.keys.every(k => int(k, -9999, 9999))));
    for (const repair of value.repairs) {
      requireInput(object(repair));
      if (repair.op === "split") {
        requireInput(fields(repair, ["op", "node", "left_count", "separator"]) &&
          int(repair.left_count, 1, 6) && int(repair.separator, -9999, 9999));
      } else {
        requireInput(fields(repair, ["op", "node", "sibling"]) && ["borrow", "merge"].includes(repair.op) &&
          int(repair.sibling, 0, 63));
      }
      requireInput(int(repair.node, 0, 63));
    }
  }
  if (canonical(value).length > 1800) throw new ResourceLimit("answer-bytes");
  return value;
}
