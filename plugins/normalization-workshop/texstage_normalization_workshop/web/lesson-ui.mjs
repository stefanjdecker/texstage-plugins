// SPDX-License-Identifier: Apache-2.0
export const local = (value, language) => value?.[String(language).startsWith("de") ? "de" : "en"] || "";
export const words = language => String(language).startsWith("de") ? {
phase:"Phase",introduce:"Einführung",open:"Offen",closed:"Geschlossen",revealed:"Aufgelöst",save:"Antwort speichern",
draft:"Lokaler Entwurf (noch nicht gespeichert).",empty:"Noch keine gespeicherte Antwort.",pending:"Gespeichert; Prüfung läuft.",
checked:"Gespeichert und geprüft. Rückmeldung nach Auflösung.",unavailable:"Gespeichert; Prüfung nicht verfügbar. Bei geöffneter Aufgabe erneut speichern.",
conflict:"Die gespeicherte Antwort oder Sitzung wurde geändert. Wählen Sie, wie es weitergeht.",reload:"Gespeicherte Antwort laden",keep:"Entwurf behalten",
bad:"Bitte mindestens eine nichtleere Relation wählen; keine doppelten Relationen.",error:"Aktion fehlgeschlagen. Erneut versuchen.",
stale:"Die Sitzung wurde geändert. Aktuelle Ansicht prüfen.",capacity:"Die Kapazitätsgrenze ist erreicht.",
form:"Höchste Normalform",witness:"FD, die die nächste Normalform verletzt",lhs:"Linke Seite (leer ist erlaubt)",rhs:"Rechte Seite",
bcnf:"Bei BCNF ist keine verletzende FD nötig.",relation:"Relation",add:"Relation hinzufügen",remove:"Entfernen",
openButton:"Antworten öffnen",closeButton:"Antworten schließen",reveal:"Lösung aufdecken",reset:"Aufgabe zurücksetzen",
received:"Gespeichert",inspect:"Privat ansehen",share:"Mit Gruppe teilen",unshare:"Teilen beenden",clear:"Auswahl aufheben",
shared:"Geteilte Antwort",selected:"Private Auswahl",worked:"Eine mögliche Lösung",accepted:"Aufgabenanforderungen erfüllt.",
incorrect:"Aufgabenanforderungen noch nicht erfüllt.",missing:"Fehlende Attribute",lossless:"Verlustfrei",preserved:"FD-erhaltend",
yes:"Ja",no:"Nein",unknown:"Nicht geprüft",weakest:"Schwächste Normalform der Teilrelationen",lost:"Nicht erhaltene FD",
keys:"Kandidatenschlüssel",notice:"Alle Attribute haben atomare Werte (1NF).",private:"Nur die Lehrperson sieht diese Auswahl.",
help:"Die linke Seite einer FD darf leer sein. Eine einzelne rechte Seite wählen."
}:{
phase:"Phase",introduce:"Introduction",open:"Open",closed:"Closed",revealed:"Revealed",save:"Save answer",
draft:"Local draft (not saved yet).",empty:"No saved answer yet.",pending:"Saved; checking is pending.",
checked:"Saved and checked. Feedback follows reveal.",unavailable:"Saved; checking unavailable. Save again when the activity is open.",
conflict:"The saved answer or session changed. Choose how to continue.",reload:"Load saved answer",keep:"Keep my draft",
bad:"Choose at least one nonempty relation, with no duplicate relations.",error:"Action failed. Please try again.",
stale:"The session changed. Check the current view.",capacity:"The capacity limit has been reached.",
form:"Highest normal form",witness:"FD that violates the next normal form",lhs:"Left side (empty is allowed)",rhs:"Right side",
bcnf:"BCNF needs no violating FD.",relation:"Relation",add:"Add relation",remove:"Remove",
openButton:"Open answers",closeButton:"Close answers",reveal:"Reveal answer",reset:"Reset activity",
received:"Saved",inspect:"Inspect privately",share:"Share with class",unshare:"Stop sharing",clear:"Clear selection",
shared:"Shared answer",selected:"Private selection",worked:"One worked answer",accepted:"The task requirements are satisfied.",
incorrect:"The task requirements are not yet satisfied.",missing:"Missing attributes",lossless:"Lossless",preserved:"FD preserving",
yes:"Yes",no:"No",unknown:"Not checked",weakest:"Weakest component normal form",lost:"Unpreserved FD",
keys:"Candidate keys",notice:"All attributes have atomic values (1NF).",private:"Only the presenter sees this selection.",
help:"An FD may have an empty left side. Choose a single right-side attribute."
};
export function el(tag, text, attrs={}) {
  const node=document.createElement(tag);
  if(text!==undefined) node.textContent=text;
  for(const [key,value] of Object.entries(attrs)) node.setAttribute(key,value);
  return node;
}
export function button(text, fn, signal) {
  const node=el("button",text,{type:"button"});node.addEventListener("click",fn,{signal});return node;
}
export function shell(ctx) {
  const root=el("section",undefined,{class:"nw-workshop",lang:String(ctx.language).startsWith("de")?"de":"en"});
  const style=el("style",`.nw-workshop{box-sizing:border-box;background:#fff;color:#17283a;padding:12px;font:16px/1.4 system-ui,sans-serif;border-radius:8px;overflow-wrap:anywhere}
.nw-workshop *{box-sizing:border-box}.nw-workshop [hidden]{display:none!important}
.nw-workshop button,.nw-workshop select{min-height:44px;max-width:100%;font:inherit;padding:7px;margin:3px;border:1px solid #688197;border-radius:5px}
.nw-workshop button{background:#edf5fa;color:#17283a;cursor:pointer}.nw-workshop button:disabled,.nw-workshop button[aria-disabled=true]{opacity:.5;cursor:default}
.nw-workshop input{min-width:20px;min-height:20px}.nw-workshop :focus-visible{outline:3px solid #b75a00;outline-offset:2px}
.nw-workshop fieldset{border:1px solid #9aaebb;border-radius:6px;min-width:0;padding:8px;margin:8px 0}
.nw-workshop .nw-pickers{display:flex;flex-wrap:wrap;gap:3px}.nw-workshop .nw-pickers label{display:flex;align-items:center;gap:6px;min-height:44px;padding:5px;border:1px solid #9aaebb;border-radius:5px}
.nw-workshop h2,.nw-workshop h3,.nw-workshop p{margin:8px 0}.nw-workshop .nw-conflict{padding:8px;border:2px solid #b75a00}
.nw-workshop .nw-answer{white-space:pre-wrap}.nw-workshop table{border-collapse:collapse;font-size:.85em}.nw-workshop td,.nw-workshop th{padding:4px;border:1px solid #9aaebb}
.nw-workshop .nw-comparison{display:grid;gap:12px;align-items:start}.nw-workshop .nw-comparison-card{min-width:0;padding:8px;border:1px solid #9aaebb;border-radius:6px}
.nw-workshop .nw-table{max-width:100%;overflow:auto}.nw-workshop .nw-table td,.nw-workshop .nw-table th{white-space:nowrap}.nw-workshop caption{text-align:left;font-weight:bold}
.nw-workshop summary{cursor:pointer;min-height:44px;padding:10px 0;font-weight:bold}.nw-workshop button[aria-pressed=true]{border:2px solid #174b72;background:#dcecf7}
`);
  root.append(style);ctx.container.append(root);return root;
}
export const attrs = (mask, item) => item.attributes.filter((_,i)=>mask & (1<<i)).map(a=>a.id).join(", ") || "∅";
export const fd = (pair,item) => attrs(pair[0],item)+" → "+attrs(pair[1],item);
export function outline(answer,item) {
  return answer.mode==="decompose" ? answer.relations.map((m,i)=>`R${i+1}(${attrs(m,item)})`).join("\n") :
    answer.normal_form.toUpperCase()+(answer.witness ? "\n"+fd(answer.witness,item) : "");
}
export function material(ctx,root,w) {
  root.append(el("h2",local(ctx.item.title,ctx.language)),el("p",local(ctx.item.prompt,ctx.language)));
  root.append(el("p",ctx.item.attributes.map(a=>a.id+": "+local(a.label,ctx.language)).join("; ")));
  root.append(el("p",ctx.item.fds.map(p=>fd(p,ctx.item)).join("; ") || "F = ∅"),el("p",w.notice));
}
export function feedback(value, item,w) {
  if(!value)return "";
  const yn=v=>v===null?w.unknown:v?w.yes:w.no;
  const rows=[value.accepted?w.accepted:w.incorrect];
  if(value.normal_form)rows.push((item.task.mode==="classify"?w.form:w.weakest)+": "+value.normal_form.toUpperCase());
  if(value.witness)rows.push(w.witness+": "+fd(value.witness,item));
  if(item.task.mode==="decompose"){
    if(value.missing)rows.push(w.missing+": "+attrs(value.missing,item));
    rows.push(w.lossless+": "+yn(value.lossless),w.preserved+": "+yn(value.preserved));
    if(value.lost_fd>=0)rows.push(w.lost+": "+fd(item.fds[value.lost_fd],item));
  }
  return rows.join("\n");
}
export function errorText(e,w) {
  if(["stale-answer","stale-epoch","stale-control","stale-phase","closed","inactive","phase","reset-required"].includes(e?.code))return w.stale;
  if(["capacity","queue-full"].includes(e?.code))return w.capacity;
  return w.error;
}
export function workedPanel(root,item,w) {
  const panel=el("section",undefined,{class:"nw-worked"}),a=el("p","",{class:"nw-answer"}),p=el("p");
  panel.append(el("h3",w.worked),a,p);root.append(panel);panel.hidden=true;
  return value=>{panel.hidden=!value;a.textContent=value?outline(value.answer,item):"";p.textContent=value?.explanation||"";};
}
