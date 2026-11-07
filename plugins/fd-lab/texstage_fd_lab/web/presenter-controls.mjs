// SPDX-License-Identifier: Apache-2.0
import {words, el, button, shell, feedback, errorText, workedPanel, renderAnswer} from "./lesson-ui.mjs";
export function mount(ctx) {
  const w = words(ctx.language), root = shell(ctx), seed = ctx.item.seed;
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
  const select = el("select", undefined, {"aria-label":w.inspect}); select.append(el("option", w.none, {value:""}));
  const previousPage = button(w.previousPage, () => send("roster-page", {page:current.data.roster_page - 1}), ctx.signal);
  const nextPage = button(w.nextPage, () => send("roster-page", {page:current.data.roster_page + 1}), ctx.signal);
  const pageLabel = el("span");
  const inspect = button(w.inspect, () => send("select-answer", {actor:select.value || null}), ctx.signal);
  const share = button(w.share, () => send("select-demonstration", {actor:select.value}), ctx.signal);
  const clear = button(w.clear, () => send("select-demonstration", {actor:null}), ctx.signal);
  const begin = button(w.beginWalk, () => send("demonstrate", {step:0}), ctx.signal);
  const prev = button(w.prev, () => send("demonstrate", {step:current.data.demo_step - 1}), ctx.signal);
  const next = button(w.nextStep, () => send("demonstrate", {step:current.data.demo_step + 1}), ctx.signal);
  const progress = el("p"), saved = el("div"), result = el("p");
  root.append(phase, open, close, reveal, reset, counts, previousPage, pageLabel, nextPage, select, inspect, share, clear,
    saved, result, begin, prev, next, progress, error);
  root.append(el("p", ctx.item.points ? `${w.maximumPoints}: ${ctx.item.points}. ${w.pointsOnReveal}` : w.noPoints));
  const worked = workedPanel(root, w, seed);
  select.addEventListener("change", () => draw(), {signal:ctx.signal});
  function draw() {
    if (!current) return;
    const d = current.data;
    const proofLength = d.worked.answer.steps?.length;
    for (const node of [begin, prev, next, progress]) node.hidden = proofLength === undefined;
    phase.textContent = `${w.phase}: ${w[d.phase]}. ${w.count}: ${d.count}.`;
    counts.textContent = w.counts + ": " + ["pending","correct","incorrect","unavailable"].map(k => d.counts[k]).join(" / ");
    for (const node of [previousPage, pageLabel, nextPage]) node.hidden = d.roster_pages <= 1;
    pageLabel.textContent = ` ${w.page} ${d.roster_page + 1} / ${d.roster_pages} `;
    previousPage.disabled = busy || d.roster_page === 0;
    nextPage.disabled = busy || d.roster_page + 1 >= d.roster_pages;
    open.disabled = busy || d.phase === "open" || (d.phase === "revealed" && ctx.item.points > 0);
    close.disabled = busy || d.phase !== "open";
    reveal.disabled = busy || !["open", "closed"].includes(d.phase);
    reset.disabled = busy; inspect.disabled = busy;
    share.disabled = busy || !select.value || d.phase !== "revealed";
    clear.disabled = busy || !d.demonstration;
    begin.disabled = busy || d.phase !== "revealed";
    prev.disabled = busy || d.phase !== "revealed" || d.demo_step === null || d.demo_step === 0;
    next.disabled = busy || d.phase !== "revealed" || d.demo_step === null || d.demo_step >= proofLength;
    progress.textContent = d.demo_step === null ? "" : `${w.step} ${d.demo_step} / ${proofLength}`;
    saved.hidden = !d.selected;
    renderAnswer(saved, seed, d.selected?.answer, w);
    result.textContent = feedback(d.selected, w, seed);
    worked(d.worked, ctx.language);
  }
  return {
    update(nextView) {
      current = nextView;
      const key = JSON.stringify(nextView.data.participants);
      if (key !== roster) {
        const selected = select.value;
        select.replaceChildren(el("option", w.none, {value:""}));
        for (const row of nextView.data.participants)
          select.append(el("option", `${w.response} ${row.number} (${w.rosterStatus[row.status]})`, {value:row.actor}));
        select.value = selected; if (select.selectedIndex < 0) select.value = "";
        roster = key;
      }
      draw();
    },
    destroy() { root.remove(); }
  };
}
