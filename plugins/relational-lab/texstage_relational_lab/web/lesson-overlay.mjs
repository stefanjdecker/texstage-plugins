// SPDX-License-Identifier: Apache-2.0
import {words, local, el, shell, outlineAnswer} from "./lesson-ui.mjs";
export function mount(ctx) {
  const w = words(ctx.language), root = shell(ctx);
  Object.assign(root.style, {position:"absolute", overflow:"auto", pointerEvents:"auto"});
  const title = el("h2", local(ctx.item.title, ctx.language)), prompt = el("p", local(ctx.item.prompt, ctx.language));
  title.hidden = prompt.hidden = true; // The frame title already identifies the exercise.
  const status = el("p"), label = el("h3"), answer = el("pre"), explanation = el("p");
  root.append(title, prompt, status, label, answer, explanation);
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
      // Presenter controls hold the private answer; the slide matches the
      // projector until reveal or an explicit demonstration.
      const worked = data.phase === "revealed" ? data.worked : null;
      const selected = data.demonstration || worked?.answer;
      // Until an answer is shared/revealed, leave the complete static exercise
      // (including its tables and baseline tree) visible beneath this mount.
      root.hidden = !placed || !selected;
      label.hidden = answer.hidden = !selected;
      label.textContent = data.demonstration ? w.shared : w.worked;
      answer.textContent = selected ? outlineAnswer(selected) : "";
      explanation.textContent = data.demonstration ? "" : local(worked?.explanation, ctx.language);
    },
    destroy() { root.remove(); }
  };
}

