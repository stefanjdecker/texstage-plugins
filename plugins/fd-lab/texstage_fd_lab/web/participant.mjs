// SPDX-License-Identifier: Apache-2.0
import {answerFor} from "./validation.mjs";
import {canonical} from "./identity.mjs";
import {lessonEditor, starter} from "./lesson-editors.mjs";
import {local, words, el, button, shell, publicMaterial, feedback, errorText, workedPanel} from "./lesson-ui.mjs";

export function mount(ctx) {
  const w = words(ctx.language), root = shell(ctx), seed = ctx.item.seed;
  publicMaterial(ctx, root, w);
  const phase = el("p"), notice = el("p", local(ctx.item.sharing_notice, ctx.language));
  root.append(phase, notice, el("p", ctx.item.feedback === "practice" ? w.practice : w.withheld), el("p", w[ctx.item.mode + "Help"]));
  let current, epoch, version = 0, dirty = false, busy = false, pending = null, hasConflict = false;
  const editor = lessonEditor(ctx, root, w, () => { dirty = true; error.textContent = ""; draw(); });
  const message = el("p", "", {role:"status", "aria-live":"polite"}), error = el("p", "", {role:"alert"});
  const conflict = el("div", undefined, {class:"fd-conflict", hidden:""}); conflict.append(el("p", w.conflict));
  const adopt = (keep = false) => {
    epoch = current.epoch; version = current.data.own?.version || 0;
    if (!keep) { editor.set(current.data.own?.answer || starter(seed)); dirty = false; }
    else dirty = true;
    hasConflict = false; pending = null; error.textContent = ""; draw();
  };
  conflict.append(button(w.reload, () => adopt(), ctx.signal), button(w.keep, () => adopt(true), ctx.signal));
  const save = button(w.save, async () => {
    if (!current || save.disabled) return;
    let answer;
    try { answer = answerFor(seed, editor.get()); }
    catch { error.textContent = ctx.item.mode === "keys" && seed.task.require === "one" ? w.needOneKey : w.bad; return; }
    pending = canonical(answer); busy = true; error.textContent = ""; draw();
    try { await ctx.dispatch("submit", {phase:current.data.phase_version, version, answer}); }
    catch (e) {
      pending = null; error.textContent = errorText(e, w);
      if (["stale-answer", "stale-epoch"].includes(e?.code)) hasConflict = true;
    } finally { busy = false; draw(); }
  }, ctx.signal);
  root.append(conflict, save, message, error);
  const worked = workedPanel(root, w, seed);
  function draw() {
    if (!current) return;
    const d = current.data;
    phase.textContent = `${w.phase}: ${w[d.phase]}. ${w.count}: ${d.count}.`;
    conflict.hidden = !hasConflict;
    save.disabled = busy || pending !== null || hasConflict || !d.active || d.phase !== "open";
    message.textContent = dirty ? w.draft : feedback(d.own, w, seed);
    worked(d.worked, ctx.language);
  }
  return {
    update(next) {
      current = next;
      const own = next.data.own, incomingVersion = own?.version || 0;
      if (epoch === undefined) adopt();
      else if (next.epoch !== epoch) {
        pending = null;
        if (dirty) hasConflict = true; else adopt();
      } else if (incomingVersion !== version) {
        if (pending && own && canonical(own.answer) === pending) {
          version = incomingVersion; dirty = canonical(editor.get()) !== pending; pending = null;
        } else if (dirty || busy || hasConflict) hasConflict = true;
        else adopt();
      }
      draw();
    },
    destroy() { root.remove(); }
  };
}
