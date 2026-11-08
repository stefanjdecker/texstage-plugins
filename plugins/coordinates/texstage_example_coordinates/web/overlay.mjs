// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
import { grid } from "./grid.mjs";
import { languageTag } from "./locale.mjs";
export function mount(ctx) {
  const panel = document.createElement("div");
  panel.lang = languageTag(ctx.language);
  Object.assign(panel.style, { position: "absolute", background: "white" });
  ctx.container.append(panel);
  const plane = grid(panel, ctx.item, undefined, undefined, ctx.language);
  return {
    place(rects) { const r = rects.box; if (!r) return;
      Object.assign(panel.style, { left: `${r.x}px`, top: `${r.y}px`, width: `${r.w}px`, height: `${r.h}px` }); },
    update({ data }) { plane.draw(data.points || [], data.answer); },
    destroy() { panel.remove(); }
  };
}
