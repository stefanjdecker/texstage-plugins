// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";

export class InputError extends Error {}
export class ResourceLimit extends Error {}
export const requireInput = condition => { if (!condition) throw new InputError("Invalid FD input"); };
export const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
export const fields = (value, names) => object(value) && Object.keys(value).length === names.length &&
  names.every(name => Object.hasOwn(value, name));
export const list = (v, lo, hi) => Array.isArray(v) && v.length >= lo && v.length <= hi;
export const id = value => typeof value === "string" && /^[a-z][a-z0-9_]{0,15}$/.test(value);
const int = (v, lo, hi) => Number.isSafeInteger(v) && v >= lo && v <= hi;
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

export function sourceFor(value) {
  requireInput(fields(value, ["format", "id", "attributes", "fds", "task"]));
  requireInput(value.format === 1 && id(value.id) && list(value.attributes, 1, 8));
  requireInput(value.attributes.every(id) && new Set(value.attributes).size === value.attributes.length);
  const maximum = (1 << value.attributes.length) - 1;
  requireInput(list(value.fds, 0, 24) && value.fds.every(fd =>
    fields(fd, ["id", "lhs", "rhs"]) && id(fd.id) && int(fd.lhs, 0, maximum) && int(fd.rhs, 1, maximum)));
  requireInput(new Set(value.fds.map(fd => fd.id)).size === value.fds.length);
  const task = value.task;
  requireInput(object(task));
  if (task.mode === "closure") requireInput(fields(task, ["mode", "start"]) && int(task.start, 0, maximum));
  else if (task.mode === "keys") requireInput(fields(task, ["mode", "require"]) && ["one", "all"].includes(task.require));
  else requireInput(fields(task, ["mode", "lhs", "rhs"]) && task.mode === "implication" &&
    int(task.lhs, 0, maximum) && int(task.rhs, 1, maximum));
  if (canonical(value).length > 32768) throw new ResourceLimit("seed-bytes");
  return value;
}

export function answerFor(seed, value) {
  requireInput(object(value) && value.format === 1 && value.mode === seed.task.mode);
  const maximum = (1 << seed.attributes.length) - 1;
  const steps = () => list(value.steps, 0, 8) && value.steps.every(i => int(i, 0, seed.fds.length - 1));
  let normalized = value;
  if (value.mode === "closure") {
    requireInput(fields(value, ["format", "mode", "closure", "steps"]) && int(value.closure, 0, maximum) && steps());
  } else if (value.mode === "keys") {
    requireInput(fields(value, ["format", "mode", "keys"]) && list(value.keys, 0, 256) &&
      value.keys.every(k => int(k, 0, maximum)) && new Set(value.keys).size === value.keys.length);
    requireInput(seed.task.require === "all" || value.keys.length === 1);
    normalized = {...value, keys: [...value.keys].sort((a, b) => a - b)};
  } else if (value.implied === true) {
    requireInput(fields(value, ["format", "mode", "implied", "steps"]) && steps());
  } else {
    requireInput(fields(value, ["format", "mode", "implied", "agree"]) && value.implied === false && int(value.agree, 0, maximum));
  }
  if (canonical(normalized).length > 1800) throw new ResourceLimit("answer-bytes");
  return normalized;
}
