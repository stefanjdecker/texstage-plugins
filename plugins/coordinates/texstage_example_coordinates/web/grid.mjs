// SPDX-FileCopyrightText: 2026 Stefan Decker
// SPDX-License-Identifier: Apache-2.0
const NS = "http://www.w3.org/2000/svg";
export function element(tag, attrs = {}, text = "") {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  if (text) e.textContent = text;
  return e;
}
export function grid(container, bounds, choose, signal) {
  const svg = element("svg", { viewBox: "0 0 400 320", role: choose ? "img" : "img",
    "aria-label": choose ? "Coordinate plane; use the X and Y fields below to enter a point with the keyboard." : "Coordinate plane with the class responses." });
  Object.assign(svg.style, { width: "100%", height: "100%", background: "white", borderRadius: "8px" });
  container.append(svg);
  const x = v => 30 + (v - bounds.xmin) / (bounds.xmax - bounds.xmin) * 340;
  const y = v => 285 - (v - bounds.ymin) / (bounds.ymax - bounds.ymin) * 260;
  function draw(points = [], answer = null) {
    svg.replaceChildren();
    for (let i = 0; i <= 10; i++) {
      const xv = bounds.xmin + i / 10 * (bounds.xmax - bounds.xmin);
      const yv = bounds.ymin + i / 10 * (bounds.ymax - bounds.ymin);
      svg.append(element("path", { d: `M${x(xv)},25V285 M30,${y(yv)}H370`, stroke: "#ddd", fill: "none" }));
      if (i % 2 === 0) svg.append(element("text", { x: x(xv), y: 307, "text-anchor": "middle", "font-size": 12 }, xv.toFixed(0)),
        element("text", { x: 25, y: y(yv) + 4, "text-anchor": "end", "font-size": 12 }, yv.toFixed(0)));
    }
    if (bounds.xmin <= 0 && bounds.xmax >= 0) svg.append(element("path", { d: `M${x(0)},25V285`, stroke: "#333" }));
    if (bounds.ymin <= 0 && bounds.ymax >= 0) svg.append(element("path", { d: `M30,${y(0)}H370`, stroke: "#333" }));
    svg.append(element("text", { x: 380, y: 310, "font-size": 14 }, "x"), element("text", { x: 8, y: 15, "font-size": 14 }, "y"));
    for (const p of points) svg.append(element("circle", { cx: x(p.x), cy: y(p.y), r: 6, fill: "#2563eb", opacity: .7 }));
    if (answer) svg.append(element("circle", { cx: x(answer.x), cy: y(answer.y), r: 10, fill: "none", stroke: "#15803d", "stroke-width": 3 }));
  }
  if (choose) svg.addEventListener("pointerup", e => {
    const cursor = svg.createSVGPoint(); cursor.x = e.clientX; cursor.y = e.clientY;
    const { x: px, y: py } = cursor.matrixTransform(svg.getScreenCTM().inverse());
    choose({ x: Math.max(bounds.xmin, Math.min(bounds.xmax, Math.round(bounds.xmin + (px - 30) / 340 * (bounds.xmax - bounds.xmin)))),
      y: Math.max(bounds.ymin, Math.min(bounds.ymax, Math.round(bounds.ymin + (285 - py) / 260 * (bounds.ymax - bounds.ymin)))) });
  }, { signal });
  draw();
  return { svg, draw };
}
