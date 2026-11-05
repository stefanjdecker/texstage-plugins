// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
export function mount(ctx) {
  const panel = document.createElement("div");
  Object.assign(panel.style, { pointerEvents: "auto", display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" });
  const status = document.createElement("span"), reveal = document.createElement("button"), reset = document.createElement("button");
  reveal.textContent = "Reveal point"; reset.textContent = "Reset responses";
  panel.append(status, reveal, reset); ctx.container.append(panel);
  panel.addEventListener("pointerdown", e => e.stopPropagation(), { signal: ctx.signal });
  for (const [button, operation] of [[reveal, "reveal"], [reset, "_reset"]]) button.addEventListener("click", async e => {
    e.stopPropagation(); button.disabled = true;
    try { await ctx.dispatch(operation, {}); }
    catch (e) { status.textContent = e.message; }
    finally { button.disabled = false; }
  }, { signal: ctx.signal });
  return {
    update({ data }) { status.textContent = `${data.count} responses · reference (${data.answer.x}, ${data.answer.y}) `;
      reveal.disabled = data.revealed; },
    destroy() { panel.remove(); }
  };
}
