// SPDX-License-Identifier: Apache-2.0
// Bounded JSON parser adapted from the collection's relational provider; owned here.
import {InputError, ResourceLimit, requireInput, text} from "./validation.mjs";
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
    if (depth > 16 || ++count > 2048) bad();
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
