// SPDX-License-Identifier: Apache-2.0
import {closureEditor} from "./closure-editor.mjs";
import {keysEditor} from "./keys-editor.mjs";
import {implicationEditor} from "./implication-editor.mjs";
export function starter(seed) {
  if (seed.task.mode === "closure") return {format:1, mode:"closure", closure:seed.task.start, steps:[]};
  if (seed.task.mode === "keys") return {format:1, mode:"keys", keys:[]};
  return {format:1, mode:"implication", implied:true, steps:[]};
}
export function lessonEditor(ctx, root, w, changed) {
  return {closure:closureEditor, keys:keysEditor, implication:implicationEditor}[ctx.item.mode](ctx, root, w, changed);
}
