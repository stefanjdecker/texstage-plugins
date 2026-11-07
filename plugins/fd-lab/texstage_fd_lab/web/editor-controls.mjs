// SPDX-License-Identifier: Apache-2.0
import {el, button, fdText, setText} from "./lesson-ui.mjs";
export function attributeSet(ctx, root, w, label, changed, prefix = w.attribute) {
  let mask = 0;
  const box = el("fieldset"); box.append(el("legend", label));
  const choices = ctx.item.seed.attributes.map((name, index) => {
    const choice = button(name, () => { mask ^= 1 << index; render(); changed(mask); }, ctx.signal);
    choice.setAttribute("aria-label", prefix + " " + name); box.append(choice); return choice;
  });
  const summary = el("p", "", {"aria-live":"polite"}); box.append(summary); root.append(box);
  function render() {
    choices.forEach((choice, i) => {
      const selected = Boolean(mask & (1 << i));
      choice.setAttribute("aria-pressed", String(selected));
      choice.textContent = (selected ? "✓ " : "") + ctx.item.seed.attributes[i];
    });
    summary.textContent = setText(ctx.item.seed, mask);
  }
  render();
  return {get:() => mask, set(value) { mask = value; render(); }};
}
export function derivation(ctx, root, w, changed) {
  let steps = [];
  const box = el("fieldset"); box.append(el("legend", w.steps));
  const cards = ctx.item.seed.fds.map((fd, index) => {
    const card = button(w.add + " " + fdText(ctx.item.seed, index), () => {
      if (steps.length >= 8) return;
      steps.push(index); render(); changed();
    }, ctx.signal);
    card.className = "fd-card"; card.setAttribute("aria-label", w.add + " " + fd.id);
    box.append(card); return card;
  });
  const history = el("ol", undefined, {"aria-label":w.steps}), empty = el("p", w.empty);
  const undo = button(w.undo, () => { steps.pop(); render(); changed(); }, ctx.signal);
  box.append(history, empty, undo); root.append(box);
  function render() {
    history.replaceChildren(...steps.map(index => el("li", fdText(ctx.item.seed, index))));
    empty.hidden = steps.length > 0; undo.disabled = steps.length === 0;
    cards.forEach(card => { card.disabled = steps.length >= 8; });
  }
  render();
  return {get:() => [...steps], set(value) { steps = [...value]; render(); }};
}
export {pairRows} from "./lesson-ui.mjs";
