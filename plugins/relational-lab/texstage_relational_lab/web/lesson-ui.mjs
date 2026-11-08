// SPDX-License-Identifier: Apache-2.0
import {answerPanel, treeOutline} from './tree-view.mjs';
import {editorWords} from './editor-text.mjs';
export const local = (value, language) => value?.[language?.startsWith("de") ? "de" : "en"] || "";
export const words = language => language?.startsWith("de") ? {
  data:"Beispieldaten", saved:"Antwort gespeichert", pending:"Gespeichert; wartet auf den Präsentationsrechner.",
  unavailable:"Die Auswertung ist nicht verfügbar. Ihre Antwort bleibt gespeichert.",
  checked:"Die Antwort besteht die konfigurierten Prüfungen.", mismatch:"Die Antwort erfüllt die Aufgabe noch nicht.",
  invalid:"Dieser Anfragebaum oder Regelschritt ist nicht gültig.", cells:"Zwischenzellen",
  worked:"Eine mögliche Lösung", shared:"Anonym geteilte Antwort", phase:"Phase", count:"Antworten",
  introduce:"Einführung", open:"Offen", closed:"Geschlossen", revealed:"Aufgelöst",
  answer:"Anfragebaum", save:"Antwort speichern", waiting:"Warte auf Bestätigung des gespeicherten Zustands…", draft:"Entwurf; noch nicht gespeichert.",
  reload:"Gespeicherte Antwort laden", keep:"Meinen Entwurf behalten",
  conflict:"Die gespeicherte Antwort oder die Aktivität hat sich geändert. Entscheiden Sie, welchen Entwurf Sie weiter bearbeiten.",
  bad:"Die Antwort ist nicht gültig oder zu groß. Prüfen Sie die markierten Knoten.",
  help:"Erstellen Sie Ihren Anfragebaum mit Tabellen und Operatoren. Die Vorschau zeigt die Bedeutung auf den Beispieldaten.",
  rewriteHelp:"Wählen Sie einen Knoten und wenden Sie eine erlaubte Regel an. Jeder Schritt verändert den aktuellen Baum.",
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
  answer:"Query tree", save:"Save answer", waiting:"Waiting for acknowledgement and saved state…", draft:"Draft; not saved yet.",
  reload:"Reload saved answer", keep:"Keep my draft",
  conflict:"The saved answer or activity has changed. Choose which draft to continue editing.",
  bad:"The answer is invalid or too large. Review the indicated nodes.",
  help:"Build your query from tables and operators. Inspect what each node produces on the example data.",
  rewriteHelp:"Select a node and apply an allowed rule. Each step changes the current tree.",
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

    .relational-lesson input{font:inherit;min-height:44px;max-width:100%;padding:8px;border:1px solid #8c9cad;border-radius:6px}
    .relational-lesson label{display:block;margin:7px 0;min-width:0}
    .relational-lesson label>input:not([type=checkbox]),.relational-lesson label>select{display:block;width:100%;margin-top:4px}
    .relational-lesson input[type=checkbox]{min-width:26px;vertical-align:middle;margin-right:8px}
    .relational-lesson fieldset{min-width:0;border:1px solid #cfdae5;border-radius:8px;padding:8px;margin:9px 0}
    .relational-lesson legend{font-weight:600}
    .relational-lesson .rl-editor{background:#f8fafc;border:1px solid #ccd8e5;border-radius:12px;padding:10px}
    .relational-lesson .rl-editor-grid,.relational-lesson .rl-comparison{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);gap:14px}
    .relational-lesson .rl-tree-list{list-style:none;padding:0;margin:8px 0}
    .relational-lesson .rl-tree-row{margin:5px 0 5px calc(var(--depth)*12px);padding-left:6px;border-left:2px solid #b9ccdf;min-width:0}
    .relational-lesson .rl-tree-row button,.relational-lesson .rl-node-label{display:block;width:100%;text-align:left;overflow-wrap:anywhere;min-height:44px;padding:8px;font-size:.95em}
    .relational-lesson .rl-tree-row [aria-pressed=true]{background:#173e62;color:#fff;border-color:#173e62}
    .relational-lesson .rl-inspector{min-width:0;border:1px solid #d6e0ea;background:white;border-radius:8px;padding:10px}
    .relational-lesson .rl-selected{font-weight:600;overflow-wrap:anywhere}
    .relational-lesson .rl-actions{display:flex;align-items:center;flex-wrap:wrap;gap:5px}
    .relational-lesson .rl-preview{margin-top:12px;padding:12px;background:#eef6fb;border:1px solid #bfd5e7;border-radius:8px;min-width:0}
    .relational-lesson .rl-note{font-size:.9em;color:#40576d}
    .relational-lesson .rl-condition{background:#f9fbfd}
    .relational-lesson .rl-column-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px 8px}
    .relational-lesson .rl-check{display:flex;align-items:center;gap:6px;min-height:44px;margin:0;overflow-wrap:anywhere}
    .relational-lesson .rl-check input{order:-1;flex:none;margin:0}
    .relational-lesson .rl-actions [aria-pressed=true]{background:#173e62;color:white}
    .relational-lesson .rl-comparison:has(>div:only-child){grid-template-columns:minmax(0,1fr)}
    .rl-overlay .rl-answer-body{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:14px}
    .rl-overlay .rl-preview{margin-top:0;padding:8px}
    .rl-overlay>p,.rl-overlay>h3{margin:2px 0}
    .rl-overlay>p:last-child{font-size:.8em}
    .rl-overlay summary{min-height:30px;padding:2px 0;font-size:.9em}
    .rl-overlay .rl-answer-panel h3{margin:3px 0}
    .rl-overlay .rl-tree-row{margin-top:2px;margin-bottom:2px}
    .rl-overlay .rl-tree-row button{font-size:.9em;margin:2px 0;padding:6px}
    .relational-lesson .rl-answer-panel{max-width:100%;overflow-wrap:anywhere}
    .relational-lesson .rl-answer-panel .rl-preview{font-size:.85em}
    @media(max-width:650px){.relational-lesson .rl-editor-grid,.relational-lesson .rl-comparison{grid-template-columns:minmax(0,1fr)}.relational-lesson{padding:8px}.relational-lesson .rl-editor{padding:6px}}
    @media(prefers-reduced-motion:reduce){.relational-lesson *{scroll-behavior:auto!important;transition:none!important}}
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
  if (ctx.item.baseline_tree) { const outline=el("div"); details.append(el("h3",w.baseline),outline); treeOutline(outline,ctx.item.baseline_tree,editorWords(ctx.language),{signal:ctx.signal}); }
  details.append(el("p", (ctx.item.mode === "rewrite" ? w.rules : w.operators) + ": " +
    (ctx.item.task.allowed_rules || ctx.item.task.allowed_operators).map(k=>editorWords(ctx.language).rules[k]||editorWords(ctx.language).labels[k]).join(", ")));
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
export function workedPanel(root, w, ctx) {
  const details=el('details',undefined,{hidden:''}); details.append(el('summary',w.worked));
  const answer=el('div'),explanation=el('p');details.append(answer,explanation);root.append(details);
  const panel=answerPanel(ctx,answer);
  const update=(worked,language)=>{details.hidden=!worked;panel.update(worked?.answer);explanation.textContent=local(worked?.explanation,language);};
  update.destroy=()=>panel.destroy();return update;
}
