// SPDX-License-Identifier: Apache-2.0
export const local = (value, language) => value?.[language?.startsWith("de") ? "de" : "en"] || "";
export const words = language => language?.startsWith("de") ? {
  data:"Beispieldaten", saved:"Antwort gespeichert", pending:"Gespeichert; wartet auf den Präsentationsrechner.",
  unavailable:"Die Auswertung ist nicht verfügbar. Ihre Antwort bleibt gespeichert.",
  checked:"Die Antwort besteht die konfigurierten Prüfungen.", mismatch:"Die Antwort erfüllt die Aufgabe noch nicht.",
  invalid:"Dieser Anfragebaum oder Regelschritt ist nicht gültig.", cells:"Zwischenzellen",
  worked:"Eine mögliche Lösung", shared:"Anonym geteilte Antwort", phase:"Phase", count:"Antworten",
  introduce:"Einführung", open:"Offen", closed:"Geschlossen", revealed:"Aufgelöst",
  answer:"Antwort als JSON", save:"Antwort speichern", draft:"Entwurf; noch nicht gespeichert.",
  reload:"Gespeicherte Antwort laden", keep:"Meinen Entwurf behalten",
  conflict:"Die gespeicherte Antwort oder die Aktivität hat sich geändert. Entscheiden Sie, welchen Entwurf Sie weiter bearbeiten.",
  bad:"Ungültiges Antwortformat. Verwenden Sie das gezeigte JSON-Format (maximal 1800 kanonische Zeichen).",
  help:"Geben Sie den Anfragebaum als JSON ein. Knoten verweisen auf frühere Knoten; der letzte Knoten ist die Wurzel.",
  rewriteHelp:"Geben Sie Regelschritte und Pfade von der Wurzel als JSON ein. Jeder Schritt bezieht sich auf den Baum nach den vorherigen Schritten.",
  openButton:"Antworten öffnen", closeButton:"Antworten schließen", reveal:"Lösung auflösen", reset:"Aktivität zurücksetzen",
  resetConfirm:"Alle Antworten in dieser Aktivität zurücksetzen?", inspect:"Antwort privat ansehen",
  share:"Ausgewählte Antwort anonym teilen", clear:"Geteilte Antwort entfernen", none:"Keine Auswahl",
  response:"Antwort", counts:"Prüfungen: ausstehend / bestanden / nicht bestanden / nicht verfügbar",
  error:"Der Befehl konnte nicht ausgeführt werden. Versuchen Sie es erneut.",
  closedError:"Antworten sind momentan geschlossen.", stale:"Der Stand hat sich geändert. Prüfen Sie die aktuelle Ansicht und versuchen Sie es erneut.",
  capacity:"Die Kapazität ist erreicht. Ihre gespeicherte Antwort bleibt erhalten.",
  queue:"Die Auswertung ist ausgelastet. Bitte versuchen Sie es erneut.",
  baseline:"Ausgangsbaum", rules:"Erlaubte Regeln", operators:"Erlaubte Operatoren"
} : {
  data:"Example data", saved:"Answer saved", pending:"Saved; waiting for the presenter's computer.",
  unavailable:"Evaluation is unavailable. Your answer remains saved.",
  checked:"The answer passes the configured checks.", mismatch:"The answer does not yet satisfy the task.",
  invalid:"This query tree or rewrite step is not valid.", cells:"Intermediate output cells",
  worked:"One worked answer", shared:"Anonymously shared answer", phase:"Phase", count:"Answers",
  introduce:"Introduction", open:"Open", closed:"Closed", revealed:"Revealed",
  answer:"Answer as JSON", save:"Save answer", draft:"Draft; not saved yet.",
  reload:"Reload saved answer", keep:"Keep my draft",
  conflict:"The saved answer or activity has changed. Choose which draft to continue editing.",
  bad:"Invalid answer format. Use the shown JSON format (at most 1800 canonical characters).",
  help:"Enter the query tree as JSON. Nodes refer to earlier nodes; the last node is the root.",
  rewriteHelp:"Enter rule applications and paths from the root as JSON. Each step applies to the tree produced by the previous steps.",
  openButton:"Open answers", closeButton:"Close answers", reveal:"Reveal solution", reset:"Reset activity",
  resetConfirm:"Reset all answers in this activity?", inspect:"Inspect an answer privately",
  share:"Share selected answer anonymously", clear:"Clear shared answer", none:"No selection",
  response:"Answer", counts:"Checks: pending / passed / not passed / unavailable",
  error:"The command could not be completed. Please retry.",
  closedError:"Answers are currently closed.", stale:"The state has changed. Check the current view and retry.",
  capacity:"Capacity has been reached. Your saved answer is preserved.",
  queue:"Evaluation is busy. Please retry.",
  baseline:"Starting tree", rules:"Allowed rules", operators:"Allowed operators"
};
export function el(tag, text, attrs = {}) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}
export function formatAnswer(answer) {
  if (!answer) return "";
  const field = answer.mode === "construct" ? "tree" : "steps";
  return '{\n  "mode": ' + JSON.stringify(answer.mode) + ',\n  "' + field + '": [\n' +
    answer[field].map(row => "    " + JSON.stringify(row)).join(",\n") + "\n  ]\n}";
}
export function outlineAnswer(answer) {
  return answer.mode === "construct"
    ? answer.tree.map((node, index) => index + ": " + JSON.stringify(node)).join("\n")
    : answer.steps.map((step, index) => (index + 1) + ". " + step.rule + " @ " + JSON.stringify(step.path)).join("\n");
}
export function button(text, handler, signal) {
  const node = el("button", text, {type:"button"});
  node.addEventListener("click", handler, {signal});
  return node;
}
export function shell(ctx) {
  const root = el("section", undefined, {class:"relational-lesson"});
  const style = el("style", `
    .relational-lesson{box-sizing:border-box;color:#182331;background:#fff;padding:12px;font:16px/1.45 system-ui,sans-serif;min-width:0;max-width:100%}
    .relational-lesson *{box-sizing:border-box}
    .relational-lesson h2{font-size:1.2em;margin:0 0 .5em}
    .relational-lesson h3{font-size:1em;margin:8px 0}
    .relational-lesson p{margin:.5em 0}
    .relational-lesson button,.relational-lesson select{font:inherit;min-height:44px;padding:6px 10px;margin:4px 4px 4px 0;max-width:100%;white-space:normal}
    .relational-lesson button{border:1px solid #75879b;border-radius:5px;background:#eaf2fa;color:#152d45;cursor:pointer}
    .relational-lesson :disabled{opacity:.55;cursor:default}
    .relational-lesson :focus-visible{outline:3px solid #247bcc;outline-offset:2px}
    .relational-lesson textarea{display:block;width:100%;font:14px/1.45 monospace;min-height:230px;resize:vertical;padding:8px}
    .relational-lesson pre{font:13px/1.4 monospace;white-space:pre-wrap;overflow-wrap:anywhere;max-height:280px;overflow:auto;background:#f3f6f9;padding:8px}
    .relational-lesson .rl-table{overflow-x:auto;margin:.5em 0}
    .relational-lesson table{border-collapse:collapse;font-size:.9em}
    .relational-lesson th,.relational-lesson td{border:1px solid #b9c5d2;padding:3px 8px;text-align:left;white-space:nowrap}
    .relational-lesson summary{cursor:pointer;min-height:44px;padding:8px 0}
    .relational-lesson .rl-conflict{padding:8px;background:#fff3d4;border-left:4px solid #9a6500}
    .relational-lesson [role=alert]{color:#92282b}
    .relational-lesson [hidden]{display:none!important}
  `);
  root.append(style); ctx.container.append(root);
  return root;
}
export function publicMaterial(ctx, root, w) {
  root.append(el("h2", local(ctx.item.title, ctx.language)), el("p", local(ctx.item.prompt, ctx.language)));
  const details = el("details"); details.append(el("summary", w.data));
  for (const [name, columns] of Object.entries(ctx.item.relations)) {
    const wrap = el("div", undefined, {class:"rl-table", tabindex:"0", "aria-label":name});
    const table = el("table"); table.append(el("caption", name));
    const head = el("tr"); for (const column of columns) head.append(el("th", column[0], {scope:"col"}));
    table.append(head);
    for (const row of ctx.item.instance.tables[name]) {
      const tr = el("tr"); for (const cell of row) tr.append(el("td", String(cell))); table.append(tr);
    }
    wrap.append(table); details.append(wrap);
  }
  if (ctx.item.baseline_tree) details.append(el("h3", w.baseline), el("pre", JSON.stringify(ctx.item.baseline_tree, null, 2)));
  details.append(el("p", (ctx.item.mode === "rewrite" ? w.rules : w.operators) + ": " +
    (ctx.item.task.allowed_rules || ctx.item.task.allowed_operators).join(", ")));
  root.append(details);
}
export function feedback(own, w) {
  if (!own) return "";
  if (own.status === "pending") return w.pending;
  if (own.status === "unavailable") return w.unavailable;
  const f = own.feedback;
  return f ? (w[f.code] || w.unavailable) + (f.cells === undefined ? "" : ` ${w.cells}: ${f.cells}.`) : w.saved;
}
export function errorText(error, w) {
  const code = error?.code || "";
  if (["closed", "item-closed"].includes(code)) return w.closedError;
  if (["stale-answer", "stale-phase", "stale-control", "stale-epoch", "stale-revision", "concurrent-update"].includes(code)) return w.stale;
  if (["capacity", "session-capacity", "reset-required"].includes(code)) return w.capacity;
  if (code === "queue-full") return w.queue;
  if (code === "invalid-answer") return w.bad;
  return w.error;
}
export function workedPanel(root, w) {
  const details = el("details", undefined, {hidden:""}); details.append(el("summary", w.worked));
  const answer = el("pre"), explanation = el("p"); details.append(answer, explanation); root.append(details);
  return (worked, language) => {
    details.hidden = !worked;
    answer.textContent = formatAnswer(worked?.answer);
    explanation.textContent = local(worked?.explanation, language);
  };
}

