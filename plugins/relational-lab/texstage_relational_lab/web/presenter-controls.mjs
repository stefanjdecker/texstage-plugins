// SPDX-License-Identifier: Apache-2.0
import {words, el, button, shell, feedback, errorText, workedPanel, formatAnswer} from "./lesson-ui.mjs";
export function mount(ctx) {
  const w = words(ctx.language), root = shell(ctx);
  const phase = el("p"), counts = el("p"), error = el("p", "", {role:"alert"});
  let current, busy = false, roster = "";
  const send = async (operation, extra = {}) => {
    if (!current || busy) return;
    busy = true; error.textContent = ""; draw();
    try { await ctx.dispatch(operation, operation === "_reset" ? {} : {control:current.data.control_version, ...extra}); }
    catch (e) { error.textContent = errorText(e, w); }
    finally { busy = false; draw(); }
  };
  const open = button(w.openButton, () => send("open"), ctx.signal);
  const close = button(w.closeButton, () => send("close"), ctx.signal);
  const reveal = button(w.reveal, () => send("reveal"), ctx.signal);
  const reset = button(w.reset, () => { if (globalThis.confirm(w.resetConfirm)) send("_reset"); }, ctx.signal);
  const select = el("select", undefined, {"aria-label":w.inspect});
  select.append(el("option", w.none, {value:""}));
  const inspect = button(w.inspect, () => send("select-answer", {actor:select.value}), ctx.signal);
  const share = button(w.share, () => send("select-demonstration", {actor:select.value}), ctx.signal);
  const clear = button(w.clear, () => send("select-demonstration", {actor:""}), ctx.signal);
  const saved = el("pre"), result = el("p");
  root.append(phase, open, close, reveal, reset, counts, select, inspect, share, clear, saved, result, error);
  const worked = workedPanel(root, w);
  select.addEventListener("change", () => draw(), {signal:ctx.signal});
  function draw() {
    if (!current) return;
    const d = current.data;
    phase.textContent = `${w.phase}: ${w[d.phase]}. ${w.count}: ${d.count}.`;
    counts.textContent = w.counts + ": " + ["pending","correct","incorrect","unavailable"].map(k => d.counts[k]).join(" / ");
    open.disabled = busy || d.phase === "open";
    close.disabled = busy || d.phase !== "open";
    reveal.disabled = busy || d.phase !== "closed";
    reset.disabled = busy; inspect.disabled = busy;
    share.disabled = busy || !select.value || !["closed","revealed"].includes(d.phase);
    clear.disabled = busy || !d.demonstration;
    saved.hidden = !d.selected;
    saved.textContent = formatAnswer(d.selected?.answer);
    result.textContent = feedback(d.selected, w);
    worked(d.worked, ctx.language);
  }
  return {
    update(next) {
      current = next;
      const key = JSON.stringify(next.data.participants);
      if (key !== roster) {
        const selected = select.value;
        select.replaceChildren(el("option", w.none, {value:""}));
        for (const row of next.data.participants) select.append(el("option", `${w.response} ${row.number} (${row.status})`, {value:row.actor}));
        select.value = selected; if (select.selectedIndex < 0) select.value = "";
        roster = key;
      }
      draw();
    },
    destroy() { root.remove(); }
  };
}

