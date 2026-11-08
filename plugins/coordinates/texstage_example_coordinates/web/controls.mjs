// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import { languageTag, words } from "./locale.mjs";
export function mount(ctx) {
  const t = words(ctx.language);
  const panel = document.createElement("div");
  panel.lang = languageTag(ctx.language);
  Object.assign(panel.style, { pointerEvents: "auto", display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" });
  const status = document.createElement("span"), reveal = document.createElement("button"), reset = document.createElement("button");
  reveal.textContent = t.reveal; reset.textContent = t.reset;
  panel.append(status, reveal, reset); ctx.container.append(panel);
  panel.addEventListener("pointerdown", e => e.stopPropagation(), { signal: ctx.signal });
  for (const [button, operation] of [[reveal, "reveal"], [reset, "_reset"]]) button.addEventListener("click", async e => {
    e.stopPropagation(); button.disabled = true;
    try { await ctx.dispatch(operation, {}); }
    catch { status.textContent = t.controlError; }
    finally { button.disabled = false; }
  }, { signal: ctx.signal });
  return {
    update({ data }) { status.textContent = `${data.count} ${t.responses} · ${t.controlReference} (${data.answer.x}, ${data.answer.y}) `;
      reveal.disabled = data.revealed; },
    destroy() { panel.remove(); }
  };
}
