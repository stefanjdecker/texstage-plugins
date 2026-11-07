// SPDX-License-Identifier: Apache-2.0
import {words, local, el, shell, renderAnswer} from "./lesson-ui.mjs";
export function mount(ctx) {
  const w = words(ctx.language), root = shell(ctx);
  root.classList.add("fd-overlay");
  Object.assign(root.style, {position:"absolute", overflow:"auto", pointerEvents:"auto"});
  const status = el("p"), label = el("h3"), answer = el("div"), explanation = el("p");
  root.append(status, label, answer, explanation);
  Object.assign(answer.style, {fontSize:".85em", lineHeight:"1.3", maxHeight:"none", overflow:"visible"});
  let placed = false;
  return {
    place(rects) {
      const box = rects.box;
      placed = Boolean(box);
      if (!box) { root.hidden = true; return; }
      Object.assign(root.style, {left:`${box.x}px`, top:`${box.y}px`, width:`${box.w}px`, height:`${box.h}px`,
        fontSize:`${Math.max(10, Math.min(22, box.w / 36))}px`});
    },
    update({data}) {
      status.textContent = `${w.phase}: ${w[data.phase]}. ${w.count}: ${data.count}.`;
      const worked = data.phase === "revealed" ? data.worked : null;
      const selected = data.demonstration || worked?.answer;
      root.hidden = !placed || !selected;
      label.textContent = data.walkthrough ? w.walkthrough : data.demonstration ? w.shared : w.worked;
      renderAnswer(answer, ctx.item.seed, selected, w, data.walkthrough, data.known);
      explanation.textContent = data.demonstration ? "" : local(worked?.explanation, ctx.language);
    },
    destroy() { root.remove(); }
  };
}
