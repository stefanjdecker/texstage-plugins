// SPDX-License-Identifier: Apache-2.0
import {el, button, setText} from "./lesson-ui.mjs";
import {attributeSet} from "./editor-controls.mjs";
export function keysEditor(ctx, root, w, changed) {
  let keys = [];
  const one = ctx.item.seed.task.require === "one";
  const selection = attributeSet(ctx, root, w, w.keySet, () => { render(); changed(); });
  const add = button(one ? w.useKey : w.addKey, () => {
    const value = selection.get();
    if (one) keys = [value];
    else if (!keys.includes(value) && keys.length < 256) keys.push(value);
    keys.sort((a,b) => a-b); render(); changed();
  }, ctx.signal);
  const list = el("ul", undefined, {"aria-label":w.proposedKeys}), empty = el("p", w.noKeys);
  root.append(el("p", w.emptyKey), add, el("h3", w.proposedKeys), list, empty);
  function render() {
    add.disabled = keys.includes(selection.get()) || (!one && keys.length >= 256);
    empty.hidden = keys.length > 0;
    list.replaceChildren(...keys.map(key => {
      const row = el("li"); row.append(el("span", setText(ctx.item.seed, key) + " "),
        button(w.removeKey + " " + setText(ctx.item.seed, key), () => {
          keys = keys.filter(value => value !== key); render(); changed();
        }, ctx.signal)); return row;
    }));
  }
  render();
  return {get:() => ({format:1, mode:"keys", keys:[...keys]}),
    set(value) { keys = [...value.keys]; selection.set(0); render(); }};
}
