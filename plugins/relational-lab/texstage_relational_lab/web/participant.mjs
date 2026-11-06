// SPDX-License-Identifier: Apache-2.0
import {answerFor, parse} from "./validation.mjs";
import {canonical} from "./identity.mjs";
import {local, words, el, button, shell, publicMaterial, feedback, errorText, workedPanel, formatAnswer} from "./lesson-ui.mjs";

export function mount(ctx) {
  const w = words(ctx.language), root = shell(ctx);
  publicMaterial(ctx, root, w);
  const phase = el("p"), notice = el("p", local(ctx.item.sharing_notice, ctx.language));
  const label = el("label", w.answer), input = el("textarea", undefined, {"aria-label":w.answer, spellcheck:"false"});
  label.append(input);
  const message = el("p", "", {role:"status", "aria-live":"polite"});
  const error = el("p", "", {role:"alert"});
  const conflict = el("div", undefined, {class:"rl-conflict", hidden:""});
  conflict.append(el("p", w.conflict));
  const starter = () => ctx.item.mode === "construct"
    ? {mode:"construct", tree:ctx.item.initial_tree} : {mode:"rewrite", steps:[]};
  let current, epoch, version = 0, dirty = false, busy = false, pending = null, hasConflict = false;
  const adopt = (keep = false) => {
    epoch = current.epoch; version = current.data.own?.version || 0;
    if (!keep) { input.value = formatAnswer(current.data.own?.answer || starter()); dirty = false; }
    else dirty = true;
    hasConflict = false; pending = null; error.textContent = ""; draw();
  };
  conflict.append(button(w.reload, () => adopt(), ctx.signal), button(w.keep, () => adopt(true), ctx.signal));
  const save = button(w.save, async () => {
    if (!current || save.disabled) return;
    let answer;
    try {
      answer = answerFor(parse(input.value, 16384));
      if (answer.mode !== ctx.item.mode) throw new Error("mode");
    } catch { error.textContent = w.bad; return; }
    pending = canonical(answer); busy = true; error.textContent = ""; draw();
    try {
      await ctx.dispatch(ctx.item.mode === "construct" ? "submit-tree" : "submit-rewrite",
        {phase:current.data.phase_version, version, answer});
    } catch (e) {
      pending = null; error.textContent = errorText(e, w);
      if (e?.code === "stale-answer" || e?.code === "stale-epoch") hasConflict = true;
    } finally { busy = false; draw(); }
  }, ctx.signal);
  input.addEventListener("input", () => { dirty = true; error.textContent = ""; draw(); }, {signal:ctx.signal});
  root.append(phase, notice, el("p", ctx.item.mode === "rewrite" ? w.rewriteHelp : w.help), label, conflict, save, message, error);
  const worked = workedPanel(root, w);
  function draw() {
    if (!current) return;
    const d = current.data;
    phase.textContent = `${w.phase}: ${w[d.phase]}. ${w.count}: ${d.count}.`;
    conflict.hidden = !hasConflict;
    save.disabled = busy || pending !== null || hasConflict || !d.active || d.phase !== "open";
    message.textContent = dirty ? w.draft : feedback(d.own, w);
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
          version = incomingVersion;
          try { dirty = canonical(answerFor(parse(input.value, 16384))) !== pending; } catch { dirty = true; }
          pending = null;
        } else if (dirty || busy || hasConflict) hasConflict = true;
        else adopt();
      }
      draw();
    },
    destroy() { root.remove(); }
  };
}

