// SPDX-License-Identifier: Apache-2.0
export async function start() { return {}; }
export function load(_library, seed) { return { options: JSON.parse(seed || "{}"), evaluations: 0 }; }
export function evaluate(state, text) {
  state.evaluations++;
  if (state.evaluations !== 1) throw new Error("Submission state was reused");
  const parts = text.trim().split(",").map(Number);
  if (parts.length !== 2 || parts.some(x => !Number.isFinite(x))) return { status: "syntax" };
  const distance = Math.hypot(...parts);
  return { status: "ok", canonical: distance.toFixed(8),
    summary: { kind: "text", text: `Distance from the origin: ${distance.toFixed(2)}` } };
}
export function dispose(state) { state.evaluations = -1; }
