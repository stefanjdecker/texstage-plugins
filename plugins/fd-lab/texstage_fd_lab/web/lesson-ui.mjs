// SPDX-License-Identifier: Apache-2.0
export const local = (value, language) => value?.[language?.startsWith("de") ? "de" : "en"] || "";
export const words = language => language?.startsWith("de") ? {
  previousPage:"Vorherige Antworten", nextPage:"Weitere Antworten", page:"Seite",
  rosterStatus:{pending:"ausstehend",correct:"korrekt",incorrect:"nicht korrekt",unavailable:"nicht verfügbar"},
  keysHelp:"Wählen Sie eine Menge und fügen Sie sie Ihrer Antwort hinzu. Ein Kandidatenschlüssel bestimmt alle Attribute und hat kein entfernbares Mitglied.",
  implicationHelp:"Entscheiden Sie, ob die Ziel-FD folgt. Geben Sie bei Ja FD-Schritte an, bei Nein ein Gegenbeispiel mit zwei Zeilen.",
  oneKey:"Finden Sie einen Kandidatenschlüssel.",
  allKeys:"Finden Sie alle Kandidatenschlüssel.",
  target:"Ziel-FD",
  keySet:"Vorgeschlagenen Schlüssel bilden",
  useKey:"Diesen Schlüssel verwenden",
  addKey:"Schlüssel hinzufügen",
  proposedKeys:"Vorgeschlagene Schlüssel",
  noKeys:"Keine Schlüssel hinzugefügt.",
  emptyKey:"Keine ausgewählten Attribute bedeuten die leere Menge ∅. Fügen Sie diese ausdrücklich als leeren Schlüssel hinzu.",
  removeKey:"Schlüssel entfernen",
  needOneKey:"Fügen Sie vor dem Speichern genau einen vorgeschlagenen Schlüssel hinzu.",
  claim:"Behauptung",
  follows:"Folgt",
  notFollows:"Folgt nicht",
  agree:"In beiden Zeilen gleiche Attribute",
  same:"In beiden Zeilen gleich:",
  row1:"Zeile 1",
  row2:"Zeile 2",
  pairHelp:"Ausgewählte Attribute sind in beiden Zeilen gleich; die übrigen unterscheiden sich. Das Paar muss alle gegebenen FDs erfüllen und die Ziel-FD verletzen.",
  keysChecked:"Ihre Antwort zu Kandidatenschlüsseln ist korrekt.",
  proofChecked:"Ihre Herleitung beweist die Ziel-FD.",
  pairChecked:"Ihre zwei Zeilen sind ein gültiges Gegenbeispiel.",
  notSuperkey:"Diese Menge bestimmt nicht alle Attribute",
  itsClosure:"Ihr Abschluss",
  notMinimal:"Dieser Superschlüssel ist nicht minimal",
  removable:"Einzeln entfernbare Mitglieder",
  missingKeys:"Noch fehlende Kandidatenschlüssel",
  invalidKeys:"Vorgeschlagene Mengen ohne Schlüsseleigenschaft",
  targetMissing:"Die Herleitung hat die Zielattribute noch nicht erreicht",
  premiseViolated:"Das Paar verletzt eine gegebene Abhängigkeit",
  targetNotViolated:"Das Paar verletzt die Ziel-FD nicht: Die linke Seite muss übereinstimmen und mindestens ein Attribut der rechten Seite muss verschieden sein.",
  start:"Startmenge", known:"Bislang bekannt", dependencies:"Gegebene FDs", steps:"Gewählte FD-Schritte", final:"Ihre endgültige Menge",
  add:"Hinzufügen", attribute:"Attribut", undo:"Letzten Schritt entfernen", empty:"Noch keine Schritte",
  closureHelp:"Fügen Sie FDs in Ihrer gewünschten Reihenfolge hinzu und wählen Sie die Attribute der endgültigen Menge. Erst Speichern prüft Ihre Antwort.",
  practice:"Übungsmodus: Nach dem Speichern erhalten Sie Feedback.", withheld:"Feedback wird bei der Auflösung freigegeben.",
  saved:"Antwort gespeichert; Feedback noch nicht freigegeben.", pending:"Gespeichert; wartet auf den Präsentationsrechner.",
  unavailable:"Die Auswertung ist nicht verfügbar. Ihre Antwort bleibt gespeichert.",
  checked:"Ihr Abschluss und Ihre Herleitung sind korrekt.", mismatch:"Die Antwort erfüllt die Aufgabe noch nicht.",
  unmet:"Für diesen Schritt fehlen Attribute der linken Seite", noop:"Dieser Schritt fügt keine neuen Attribute hinzu",
  incomplete:"Die Herleitung ist noch unvollständig", overclaimed:"Diese Attribute sind nicht ableitbar",
  finalSet:"Ihre gewählte endgültige Menge stimmt nicht mit dem Abschluss überein", next:"Nächste mögliche FD",
  step:"Schritt", missing:"Noch ableitbar", worked:"Eine mögliche Lösung", shared:"Anonym geteilte Antwort",
  walkthrough:"Schrittweise Herleitung", beginWalk:"Herleitung beginnen", prev:"Vorheriger Schritt", nextStep:"Nächster Schritt",
  phase:"Phase", count:"Antworten", introduce:"Einführung", open:"Offen", closed:"Geschlossen", revealed:"Aufgelöst",
  save:"Antwort speichern", draft:"Entwurf; noch nicht gespeichert.", reload:"Gespeicherte Antwort laden", keep:"Meinen Entwurf behalten",
  conflict:"Die gespeicherte Antwort oder Aktivität hat sich geändert. Wählen Sie, welchen Entwurf Sie weiter bearbeiten.",
  bad:"Ungültige Antwort. Prüfen Sie die ausgewählten Mengen und FD-Schritte.",
  openButton:"Antworten öffnen", closeButton:"Antworten schließen", reveal:"Lösung auflösen", reset:"Aktivität zurücksetzen",
  resetConfirm:"Alle Antworten in dieser Aktivität zurücksetzen?", inspect:"Antwort privat ansehen",
  share:"Ausgewählte Antwort anonym teilen", clear:"Geteilte Antwort entfernen", none:"Keine Auswahl", response:"Antwort",
  counts:"Prüfungen: ausstehend / bestanden / nicht bestanden / nicht verfügbar",
  error:"Der Befehl konnte nicht ausgeführt werden. Bitte erneut versuchen.", closedError:"Antworten sind momentan geschlossen.",
  stale:"Der Stand hat sich geändert. Prüfen Sie die aktuelle Ansicht und versuchen Sie es erneut.",
  capacity:"Die Kapazität ist erreicht. Ihre Antwort bleibt erhalten.", queue:"Die Auswertung ist ausgelastet. Bitte erneut versuchen."
} : {
  previousPage:"Previous answers", nextPage:"More answers", page:"Page",
  rosterStatus:{pending:"pending",correct:"correct",incorrect:"incorrect",unavailable:"unavailable"},
  keysHelp:"Select a set and add it to your answer. A candidate key determines all attributes and has no removable member.",
  implicationHelp:"Choose whether the target follows. Supply FD steps for yes, or a two-row counterexample for no.",
  oneKey:"Find one candidate key.",
  allKeys:"Find all candidate keys.",
  target:"Target FD",
  keySet:"Build a proposed key",
  useKey:"Use this key",
  addKey:"Add key",
  proposedKeys:"Proposed keys",
  noKeys:"No keys added.",
  emptyKey:"No selected attributes means the empty set, ∅. Add it explicitly to propose the empty key.",
  removeKey:"Remove key",
  needOneKey:"Add exactly one proposed key before saving.",
  claim:"Claim",
  follows:"Follows",
  notFollows:"Does not follow",
  agree:"Attributes equal in both rows",
  same:"Same in both rows:",
  row1:"Row 1",
  row2:"Row 2",
  pairHelp:"Selected attributes are equal in both rows; other attributes differ. The pair must satisfy every given FD and violate the target.",
  keysChecked:"Your candidate-key answer is correct.",
  proofChecked:"Your derivation proves the target FD.",
  pairChecked:"Your two rows are a valid counterexample.",
  notSuperkey:"This set does not determine every attribute",
  itsClosure:"Its closure",
  notMinimal:"This superkey is not minimal",
  removable:"Members removable individually",
  missingKeys:"Candidate keys still missing",
  invalidKeys:"Proposed sets that are not candidate keys",
  targetMissing:"The derivation has not reached the target attributes",
  premiseViolated:"The pair violates a given dependency",
  targetNotViolated:"The pair does not violate the target: its left side must agree and at least one right-side attribute must differ.",
  start:"Starting set", known:"Known so far", dependencies:"Given FDs", steps:"Chosen FD steps", final:"Your final set",
  add:"Add", attribute:"Attribute", undo:"Undo last step", empty:"No steps yet",
  closureHelp:"Add FDs in the order you use them, then select the attributes of your final set. Saving checks your answer.",
  practice:"Practice mode: feedback is available after saving.", withheld:"Feedback is released when the presenter reveals the solution.",
  saved:"Answer saved; feedback is withheld.", pending:"Saved; waiting for the presenter's computer.",
  unavailable:"Evaluation is unavailable. Your answer remains saved.",
  checked:"Your closure and derivation are correct.", mismatch:"The answer does not yet satisfy the task.",
  unmet:"This step needs more left-side attributes", noop:"This step adds no new attributes",
  incomplete:"The derivation is incomplete", overclaimed:"These attributes do not follow",
  finalSet:"Your selected final set differs from the complete closure", next:"One possible next FD",
  step:"Step", missing:"Still derivable", worked:"One worked answer", shared:"Anonymously shared answer",
  walkthrough:"Step-by-step derivation", beginWalk:"Start walkthrough", prev:"Previous step", nextStep:"Next step",
  phase:"Phase", count:"Answers", introduce:"Introduction", open:"Open", closed:"Closed", revealed:"Revealed",
  save:"Save answer", draft:"Draft; not saved yet.", reload:"Reload saved answer", keep:"Keep my draft",
  conflict:"The saved answer or activity has changed. Choose which draft to continue editing.",
  bad:"Invalid answer. Check the selected sets and proof steps.",
  openButton:"Open answers", closeButton:"Close answers", reveal:"Reveal solution", reset:"Reset activity",
  resetConfirm:"Reset all answers in this activity?", inspect:"Inspect an answer privately",
  share:"Share selected answer anonymously", clear:"Clear shared answer", none:"No selection", response:"Answer",
  counts:"Checks: pending / passed / not passed / unavailable",
  error:"The command could not be completed. Please retry.", closedError:"Answers are currently closed.",
  stale:"The state has changed. Check the current view and retry.",
  capacity:"Capacity has been reached. Your answer is preserved.", queue:"Evaluation is busy. Please retry."
};
export function el(tag, text, attrs = {}) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}
export function button(text, handler, signal) {
  const node = el("button", text, {type:"button"});
  node.addEventListener("click", handler, {signal});
  return node;
}
export const setText = (seed, mask) => mask === 0 ? "∅" : "{" + seed.attributes.filter((_, i) => mask & (1 << i)).join(", ") + "}";
export const fdText = (seed, index) => {
  const fd = seed.fds[index];
  return `${fd.id}: ${setText(seed, fd.lhs)} → ${setText(seed, fd.rhs)}`;
};
export function outlineAnswer(seed, answer, w, walkthrough = false, known) {
  if (!answer) return "";
  if (answer.mode === "keys") return w.proposedKeys + ":\n" + (answer.keys.length ? answer.keys.map(key => setText(seed, key)).join("\n") : w.noKeys);
  if (answer.mode === "implication" && !answer.implied) return [w.claim + ": " + w.notFollows,
    w.attribute + " | " + w.row1 + " | " + w.row2,
    ...seed.attributes.map((name, i) => name + " | 0 | " + (answer.agree & (1 << i) ? "0" : "1"))].join("\n");
  const closure = answer.mode === "closure";
  const rows = [w.start + ": " + setText(seed, closure ? seed.task.start : seed.task.lhs),
    ...answer.steps.map((index, i) => (i+1) + ". " + fdText(seed, index))];
  if (walkthrough) rows.push(w.known + ": " + setText(seed, known ?? answer.closure));
  else if (closure) rows.push(w.final + ": " + setText(seed, answer.closure));
  else rows.unshift(w.claim + ": " + w.follows);
  return rows.join("\n");
}
export function shell(ctx) {
  const root = el("section", undefined, {class:"fd-lesson"});
  root.append(el("style", `
    .fd-lesson{box-sizing:border-box;color:#182b3b;background:#fff;padding:12px;font:16px/1.45 system-ui,sans-serif;min-width:0;max-width:100%;overflow-wrap:anywhere}
    .fd-lesson *{box-sizing:border-box}.fd-lesson h2{font-size:1.2em;margin:0 0 .5em}.fd-lesson h3{font-size:1em;margin:8px 0}
    .fd-lesson p{margin:.5em 0}.fd-lesson button,.fd-lesson select{font:inherit;min-height:44px;padding:7px 10px;margin:4px 4px 4px 0;max-width:100%;white-space:normal}
    .fd-lesson button{border:1px solid #687f95;border-radius:6px;background:#edf4fb;color:#153b58;cursor:pointer}
    .fd-lesson button[aria-pressed=true]{background:#d7f1e8;border-color:#186955;font-weight:600}
    .fd-lesson .fd-card{display:block;width:100%;text-align:left;margin-right:0}
    .fd-lesson :disabled{opacity:.55;cursor:default}.fd-lesson :focus-visible{outline:3px solid #247bcc;outline-offset:2px}
    .fd-lesson pre{font:inherit;white-space:pre-wrap;overflow-wrap:anywhere;max-height:320px;overflow:auto;background:#f0f5f8;padding:8px}
    .fd-lesson summary{cursor:pointer;min-height:44px;padding:8px 0}.fd-lesson [role=alert]{color:#92282b}
    .fd-lesson .fd-conflict{padding:8px;background:#fff3d4;border-left:4px solid #9a6500}
    .fd-lesson [hidden]{display:none!important}.fd-lesson fieldset{min-width:0;border:1px solid #b9c7d2;margin:12px 0;padding:8px}
    .fd-lesson .fd-pair{border-collapse:collapse;width:100%;margin:10px 0}.fd-lesson .fd-pair th,.fd-lesson .fd-pair td{padding:5px;border-bottom:1px solid #b9c7d2;text-align:left}
    .fd-lesson.fd-overlay pre{font:inherit;max-height:none;overflow:visible}
    .fd-lesson.fd-overlay{padding:.5em}.fd-lesson.fd-overlay p,.fd-lesson.fd-overlay h3{margin:.3em 0}
    .fd-lesson.fd-overlay .fd-pair th,.fd-lesson.fd-overlay .fd-pair td{padding:.2em .25em}
    .fd-lesson legend{font-weight:600}.fd-lesson ol{padding-left:24px}
  `));
  ctx.container.append(root);
  return root;
}
export function publicMaterial(ctx, root, w) {
  const seed = ctx.item.seed, task = seed.task;
  root.append(el("h2", local(ctx.item.title, ctx.language)), el("p", local(ctx.item.prompt, ctx.language)));
  if (task.mode === "keys") root.append(el("p", task.require === "one" ? w.oneKey : w.allKeys));
  else root.append(el("p", task.mode === "closure" ? w.start + ": " + setText(seed, task.start) :
    w.target + ": " + setText(seed, task.lhs) + " → " + setText(seed, task.rhs)));
  const details = el("details"); details.append(el("summary", w.dependencies));
  for (const [index] of seed.fds.entries()) details.append(el("p", fdText(seed, index)));
  for (const attribute of ctx.item.attributes) details.append(el("p", attribute.id + ": " + local(attribute.label, ctx.language)));
  root.append(details);
}
export function feedback(own, w, seed) {
  if (!own) return "";
  if (own.status === "pending") return w.pending;
  if (own.status === "unavailable") return w.unavailable;
  const f = own.feedback;
  if (!f) return w.saved;
  if (f.code === "checked") return own.answer.mode === "keys" ? w.keysChecked :
    own.answer.mode === "implication" ? (own.answer.implied ? w.proofChecked : w.pairChecked) : w.checked;
  if (f.code !== "mismatch") return w[f.code] || w.unavailable;
  if (own.answer.mode === "keys") {
    let message = f.reason === "not-superkey" ? w.notSuperkey + ": " + setText(seed, f.key) + ". " + w.itsClosure + ": " + setText(seed, f.key_closure) + "." :
      f.reason === "not-minimal" ? w.notMinimal + ": " + setText(seed, f.key) + ". " + w.removable + ": " + setText(seed, f.removable) + "." : "";
    if (f.invalid_keys) message += " " + w.invalidKeys + ": " + f.invalid_keys + ".";
    if (f.missing_keys) message += " " + w.missingKeys + ": " + f.missing_keys + ".";
    return message.trim();
  }
  if (f.reason === "premise-violated") return w.premiseViolated + ": " + fdText(seed, f.fd) + ".";
  if (f.reason === "target-not-violated") return w.targetNotViolated;
  if (f.reason === "target-missing") return w.targetMissing + ": " + setText(seed, f.missing) + ".";
  let explanation = f.reason === "unmet-lhs" ? `${w.step} ${f.step+1}: ${w.unmet}: ${setText(seed, f.needed)}.` :
    f.reason === "no-progress" ? `${w.step} ${f.step+1}: ${w.noop}.` :
    f.reason === "overclaimed" ? `${w.overclaimed}: ${setText(seed, f.extra)}.` :
    f.reason === "final-set" ? w.finalSet + "." : w.incomplete + ".";
  if (f.missing) explanation += ` ${w.missing}: ${setText(seed, f.missing)}.`;
  if (f.next_fd >= 0) explanation += ` ${w.next}: ${seed.fds[f.next_fd].id}.`;
  return explanation;
}
export function errorText(error, w) {
  const code = error?.code || "";
  if (["closed", "item-closed"].includes(code)) return w.closedError;
  if (["stale-answer", "stale-phase", "stale-control", "stale-epoch", "stale-revision", "concurrent-update"].includes(code)) return w.stale;
  if (["capacity", "actor-capacity", "session-capacity", "reset-required"].includes(code)) return w.capacity;
  if (code === "queue-full") return w.queue;
  if (code === "invalid-answer") return w.bad;
  if (["worker-timeout", "worker-unavailable", "environment-changed"].includes(code)) return w.unavailable;
  return w.error;
}
export function workedPanel(root, w, seed) {
  const details = el("details", undefined, {hidden:""}); details.append(el("summary", w.worked));
  const answer = el("div"), explanation = el("p"); details.append(answer, explanation); root.append(details);
  return (worked, language) => {
    details.hidden = !worked;
    renderAnswer(answer, seed, worked?.answer, w);
    explanation.textContent = local(worked?.explanation, language);
  };
}

export function pairRows(root, seed, w) {
  const table = el("table", undefined, {class:"fd-pair"});
  const head = el("tr");
  for (const text of [w.attribute, w.row1, w.row2]) head.append(el("th", text, {scope:"col"}));
  const thead = el("thead"); thead.append(head); table.append(thead);
  const body = el("tbody"); table.append(body); root.append(table);
  return agree => {
    body.replaceChildren(...seed.attributes.map((name, i) => {
      const row = el("tr"); row.append(el("th", name, {scope:"row"}), el("td", "0"), el("td", agree & (1 << i) ? "0" : "1"));
      return row;
    }));
  };
}

export function renderAnswer(root, seed, answer, w, walkthrough = false, known) {
  root.replaceChildren();
  if (!answer) return;
  if (answer.mode === "implication" && !answer.implied) {
    root.append(el("p", w.claim + ": " + w.notFollows));
    pairRows(root, seed, w)(answer.agree);
  } else root.append(el("pre", outlineAnswer(seed, answer, w, walkthrough, known)));
}
