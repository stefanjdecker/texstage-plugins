// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import { grid } from "./grid.mjs";
export function mount(ctx) {
  const panel = document.createElement("section"), title = document.createElement("h2"), planeBox = document.createElement("div");
  title.textContent = "Choose your point";
  Object.assign(panel.style, { padding: "16px", maxWidth: "550px", margin: "auto" });
  planeBox.style.height = "280px";
  const form = document.createElement("form"), x = document.createElement("input"), y = document.createElement("input");
  const button = document.createElement("button"), feedback = document.createElement("p");
  for (const [field, labelText] of [[x, "X coordinate"], [y, "Y coordinate"]]) {
    const label = document.createElement("label"); label.textContent = labelText;
    field.type = "number"; field.step = "any"; field.required = true; field.value = "0";
    field.min = ctx.item[labelText[0].toLowerCase() + "min"]; field.max = ctx.item[labelText[0].toLowerCase() + "max"];
    label.append(field); form.append(label);
  }
  button.textContent = "Send point"; button.type = "submit";
  Object.assign(button.style, { minHeight: "44px", padding: "10px 16px", fontSize: "1rem", background: "#4c1d95",
    color: "white", border: "0", borderRadius: "8px", width: "100%", marginTop: "12px" });
  feedback.setAttribute("role", "status"); feedback.setAttribute("aria-live", "polite");
  form.append(button); panel.append(title, planeBox, form, feedback); ctx.container.append(panel);
  const plane = grid(planeBox, ctx.item, p => { x.value = p.x; y.value = p.y; preview(); }, ctx.signal);
  let state = null;
  const preview = () => plane.draw([{ x: Number(x.value), y: Number(y.value) }], state?.answer);
  for (const field of [x, y]) field.addEventListener("input", preview, { signal: ctx.signal });
  form.addEventListener("submit", async e => {
    e.preventDefault(); button.disabled = true; feedback.textContent = "Sending…";
    try { await ctx.dispatch("submit-point", { x: Number(x.value), y: Number(y.value) }); }
    catch (e) { feedback.textContent = e.message; }
    finally { button.disabled = !state?.active; }
  }, { signal: ctx.signal });
  return {
    update({ data }) { state = data; button.disabled = !data.active; preview();
      if (data.own) {
        const p = data.own;
        feedback.textContent = p.status === "queued" ? "Point received. Waiting for the presenter’s computer…" :
          p.feedback || `Evaluation: ${p.status}`;
        if (data.revealed) feedback.textContent += p.correct ? " · Correct point!" : ` · Reference: (${data.answer.x}, ${data.answer.y})`;
      } else feedback.textContent = "Tap the plane or enter coordinates, then send your point.";
    }, destroy() { panel.remove(); }
  };
}
