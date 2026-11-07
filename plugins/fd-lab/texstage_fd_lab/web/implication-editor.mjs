// SPDX-License-Identifier: Apache-2.0
import {el, button} from "./lesson-ui.mjs";
import {attributeSet, derivation, pairRows} from "./editor-controls.mjs";
export function implicationEditor(ctx, root, w, changed) {
  let implied = true;
  const choice = el("fieldset"); choice.append(el("legend", w.claim));
  const yes = button(w.follows, () => { implied = true; render(); changed(); }, ctx.signal);
  const no = button(w.notFollows, () => { implied = false; render(); changed(); }, ctx.signal);
  choice.append(yes, no); root.append(choice);
  const proofBox = el("div"), pairBox = el("div"); root.append(proofBox, pairBox);
  const proof = derivation(ctx, proofBox, w, changed);
  pairBox.append(el("p", w.pairHelp));
  const agreement = attributeSet(ctx, pairBox, w, w.agree, () => { drawPair(agreement.get()); changed(); }, w.same);
  const drawPair = pairRows(pairBox, ctx.item.seed, w);
  agreement.set(ctx.item.seed.task.lhs);
  function render() {
    yes.setAttribute("aria-pressed", String(implied)); no.setAttribute("aria-pressed", String(!implied));
    proofBox.hidden = !implied; pairBox.hidden = implied; drawPair(agreement.get());
  }
  render();
  return {get:() => implied ? {format:1, mode:"implication", implied:true, steps:proof.get()} :
      {format:1, mode:"implication", implied:false, agree:agreement.get()},
    set(value) {
      implied = value.implied; proof.set(value.steps || []);
      agreement.set(value.implied ? ctx.item.seed.task.lhs : value.agree); render();
    }};
}
