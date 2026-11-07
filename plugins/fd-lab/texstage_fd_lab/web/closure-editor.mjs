// SPDX-License-Identifier: Apache-2.0
import {attributeSet, derivation} from "./editor-controls.mjs";
export function closureEditor(ctx, root, w, changed) {
  const proof = derivation(ctx, root, w, changed);
  const final = attributeSet(ctx, root, w, w.final, changed);
  final.set(ctx.item.seed.task.start);
  return {
    get:() => ({format:1, mode:"closure", closure:final.get(), steps:proof.get()}),
    set(value) { proof.set(value.steps); final.set(value.closure); }
  };
}
