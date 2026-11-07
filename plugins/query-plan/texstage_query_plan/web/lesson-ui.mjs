// SPDX-License-Identifier: Apache-2.0
import {analyze} from "./model.mjs";
export const local=(value,language)=>value?.[language?.startsWith("de")?"de":"en"]||"";
const en={
 title:"Query-plan challenge",dismiss:"Close controls",pendingLabel:"Pending",unavailableLabel:"Unavailable",goalBest:"Find the least expensive feasible plan.",goalBudget:"Find a feasible plan costing at most",
 units:"Teaching cost units; these are not measured database timings.",context:"Query, statistics and cost rules",query:"Fixed query",output:"Output",
 rows:"Rows",pages:"Pages",width:"Row width (bytes)",filtered:"Output rows",hashLimit:"Hash workspace limit per join",bytes:"bytes",
 seq:"Sequential scan",index:"Index scan",nested:"Nested loop",hash:"Hash join",left:"Left input",right:"Right input",
 order:"Join order",scan:"Scan",join:"Join",method:"Method",build:"Build hash table from",noIndex:"No eligible index",tooLarge:"exceeds the workspace limit",
 estimate:"Estimate my plan",preview:"Local estimate",previewHint:"Estimate the draft before submitting. This does not save or grade it.",
 stalePreview:"Plan changed; estimate again to inspect its costs.",baseline:"Baseline cost",draftCost:"Draft cost",difference:"Difference from baseline",
 tree:"Plan tree",inspectNode:"Inspect node",node:"Node",localCost:"Operator cost",totalCost:"Subtree cost",workspace:"Hash workspace",
 arithmetic:"Arithmetic",children:"Inputs",root:"Result",undo:"Undo edit",resetDraft:"Reset draft to baseline",save:"Submit plan",
 dirty:"Draft changes have not been submitted.",saved:"Plan saved.",saving:"Submitting plan…",pending:"Plan saved; evaluation is pending.",
 unavailable:"Evaluation is unavailable. Your plan remains saved; retry while answers are open.",empty:"No plan submitted yet.",
 "goal-met":"Goal met", "target-missed":"Goal not met",invalid:"Invalid plan",
 "invalid-tree":"The plan is not a valid tree.", "unknown-relation":"Unknown relation.", "duplicate-relation":"A relation occurs more than once.",
 "missing-relation":"A relation is missing.", "disconnected-join":"This join has no connecting predicate.",
 "unavailable-index":"This relation has no eligible index.", "hash-memory":"The chosen hash input exceeds the workspace limit.",
 unsupported:"This saved plan cannot be edited with the selectors. Reset the draft to the baseline to repair it.",
 reload:"Load saved plan",keep:"Keep my draft",
 conflict:"The activity was reset or your plan changed on another device. Choose which draft to continue with.",
 introduce:"Introduction",open:"Open",closed:"Closed",revealed:"Revealed",phase:"Phase",count:"Plans submitted",
 notice:"Only your latest submitted plan is kept. The presenter may share it anonymously. Feedback is released with the solution.",
 openButton:"Open answers",closeButton:"Close answers",reveal:"Reveal solution",reset:"Reset activity",
 resetConfirm:"Clear every submitted plan and start a new round?",confirm:"Yes, reset activity",cancel:"Cancel",
 inspect:"Inspect privately",select:"Choose a submitted plan",none:"No selection",response:"Plan",share:"Share selected plan anonymously",clear:"Clear shared plan",
 private:"Private presenter view",shared:"Anonymously shared plan",worked:"Worked solution",optimal:"Optimal plan",minimum:"Minimum cost",ties:"Optimal plans",
 error:"The action failed. Your draft is preserved; please retry.",stale:"The activity changed. Review the current view before retrying.",
 closedError:"Answers are closed.",capacity:"The session is full. Your draft is preserved.",queue:"Evaluation is busy. Please retry.",
 waiting:"Waiting for the classroom update…",unknown:"No estimate",notes:"Cost rules",
 rules:"Scan: 100 × pages + base rows. Index: 400 × (height + output rows) + output rows. Nested loop: left rows × right rows + output rows. Hash: 2 × build rows + probe rows + output rows. Hash workspace: build rows × (build width + 16). A join's subtree cost adds both child costs once. Widths add; duplicate rows are retained.",
 baselineReset:"The baseline is now your draft.",retry:"Submit again"
};
const de={
 title:"Anfrageplan-Challenge",dismiss:"Bedienfeld schließen",pendingLabel:"Ausstehend",unavailableLabel:"Nicht verfügbar",goalBest:"Finden Sie den günstigsten zulässigen Plan.",goalBudget:"Finden Sie einen zulässigen Plan mit Kosten von höchstens",
 units:"Lehrmodell-Kosteneinheiten; keine gemessenen Datenbanklaufzeiten.",context:"Anfrage, Statistiken und Kostenregeln",query:"Feste Anfrage",output:"Ausgabe",
 rows:"Zeilen",pages:"Seiten",width:"Zeilenbreite (Bytes)",filtered:"Ausgabezeilen",hashLimit:"Hash-Speicherlimit je Join",bytes:"Bytes",
 seq:"Sequenzieller Scan",index:"Index-Scan",nested:"Geschachtelte Schleife",hash:"Hash-Join",left:"Linke Eingabe",right:"Rechte Eingabe",
 order:"Join-Reihenfolge",scan:"Scan",join:"Join",method:"Methode",build:"Hash-Tabelle aufbauen aus",noIndex:"Kein geeigneter Index",tooLarge:"überschreitet das Speicherlimit",
 estimate:"Meinen Plan schätzen",preview:"Lokale Schätzung",previewHint:"Schätzen Sie den Entwurf vor dem Absenden. Dies speichert und bewertet ihn noch nicht.",
 stalePreview:"Plan geändert; für aktuelle Kosten erneut schätzen.",baseline:"Ausgangskosten",draftCost:"Entwurfskosten",difference:"Differenz zum Ausgangsplan",
 tree:"Planbaum",inspectNode:"Knoten untersuchen",node:"Knoten",localCost:"Operatorkosten",totalCost:"Teilbaumkosten",workspace:"Hash-Speicher",
 arithmetic:"Berechnung",children:"Eingaben",root:"Ergebnis",undo:"Änderung rückgängig",resetDraft:"Entwurf auf Ausgangsplan setzen",save:"Plan absenden",
 dirty:"Änderungen am Entwurf sind noch nicht abgesendet.",saved:"Plan gespeichert.",saving:"Plan wird abgesendet…",pending:"Plan gespeichert; Auswertung steht aus.",
 unavailable:"Die Auswertung ist nicht verfügbar. Ihr Plan bleibt gespeichert; bei offener Aktivität erneut absenden.",empty:"Noch kein Plan abgesendet.",
 "goal-met":"Ziel erreicht","target-missed":"Ziel nicht erreicht",invalid:"Ungültiger Plan",
 "invalid-tree":"Der Plan ist kein gültiger Baum.","unknown-relation":"Unbekannte Relation.","duplicate-relation":"Eine Relation kommt mehrfach vor.",
 "missing-relation":"Eine Relation fehlt.","disconnected-join":"Für diesen Join fehlt ein verbindendes Prädikat.",
 "unavailable-index":"Für diese Relation gibt es keinen geeigneten Index.","hash-memory":"Die gewählte Hash-Eingabe überschreitet das Speicherlimit.",
 unsupported:"Dieser gespeicherte Plan kann nicht mit den Auswahlfeldern bearbeitet werden. Setzen Sie den Entwurf zur Reparatur auf den Ausgangsplan.",
 reload:"Gespeicherten Plan laden",keep:"Meinen Entwurf behalten",
 conflict:"Die Aktivität wurde zurückgesetzt oder Ihr Plan auf einem anderen Gerät geändert. Wählen Sie den Entwurf zum Weiterarbeiten.",
 introduce:"Einführung",open:"Offen",closed:"Geschlossen",revealed:"Aufgelöst",phase:"Phase",count:"Abgesendete Pläne",
 notice:"Nur Ihr zuletzt abgesendeter Plan bleibt gespeichert. Die Lehrperson kann ihn anonym teilen. Feedback erscheint mit der Lösung.",
 openButton:"Antworten öffnen",closeButton:"Antworten schließen",reveal:"Lösung zeigen",reset:"Aktivität zurücksetzen",
 resetConfirm:"Alle abgesendeten Pläne löschen und eine neue Runde starten?",confirm:"Ja, Aktivität zurücksetzen",cancel:"Abbrechen",
 inspect:"Privat ansehen",select:"Abgesendeten Plan auswählen",none:"Keine Auswahl",response:"Plan",share:"Gewählten Plan anonym teilen",clear:"Geteilten Plan entfernen",
 private:"Private Präsentationsansicht",shared:"Anonym geteilter Plan",worked:"Beispiellösung",optimal:"Optimaler Plan",minimum:"Minimale Kosten",ties:"Optimale Pläne",
 error:"Die Aktion ist fehlgeschlagen. Ihr Entwurf bleibt erhalten; bitte erneut versuchen.",stale:"Die Aktivität hat sich geändert. Prüfen Sie den aktuellen Stand.",
 closedError:"Antworten sind geschlossen.",capacity:"Die Sitzung ist voll. Ihr Entwurf bleibt erhalten.",queue:"Die Auswertung ist ausgelastet. Bitte erneut versuchen.",
 waiting:"Warten auf die Aktualisierung…",unknown:"Keine Schätzung",notes:"Kostenregeln",
 rules:"Scan: 100 × Seiten + Basiszeilen. Index: 400 × (Höhe + Ausgabezeilen) + Ausgabezeilen. Geschachtelte Schleife: linke Zeilen × rechte Zeilen + Ausgabezeilen. Hash: 2 × Aufbauzeilen + Probezeilen + Ausgabezeilen. Hash-Speicher: Aufbauzeilen × (Aufbaubreite + 16). Teilbaumkosten enthalten beide Kindkosten genau einmal. Breiten werden addiert; Duplikate bleiben erhalten.",
 baselineReset:"Der Ausgangsplan ist jetzt Ihr Entwurf.",retry:"Erneut absenden"
};
export const words=language=>language?.startsWith("de")?de:en;
export const number=(n,language)=>Number.isFinite(n)?n.toLocaleString(language?.startsWith("de")?"de-DE":"en-GB"):"–";
export function el(tag,text,attrs={}) {
 const n=document.createElement(tag);if(text!==undefined)n.textContent=text;
 for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n;
}
export function button(text,fn,signal){const n=el("button",text,{type:"button"});n.addEventListener("click",fn,{signal});return n;}
export function field(text,control){const label=el("label",undefined,{class:"qp-field"});label.append(el("span",text),control);return label;}
export function option(value,text,disabled=false){const n=el("option",text,{value});n.disabled=disabled;return n;}
export function details(title){const n=el("details");n.append(el("summary",title));return n;}
export function shell(ctx,kind=""){
 const root=el("section",undefined,{class:"qp-lesson "+kind,"aria-label":words(ctx.language).title});
 root.append(el("style",`
 .qp-lesson{box-sizing:border-box;background:#fff;color:#162d40;font:16px/1.45 system-ui,sans-serif;padding:14px;min-width:0;max-width:100%;overflow-wrap:anywhere;border-radius:8px}
 .qp-lesson *{box-sizing:border-box}
 .qp-lesson [hidden]{display:none!important}
 .qp-lesson h2{font-size:1.25em;margin:0 0 .5em}.qp-lesson h3{font-size:1.05em;margin:.8em 0 .4em}
 .qp-lesson p{margin:.5em 0}.qp-lesson small{font-size:.85em}
 .qp-lesson button,.qp-lesson select{font:inherit;min-height:44px;max-width:100%;padding:8px;border:1px solid #75889b;border-radius:5px}
 .qp-lesson button{background:#edf3f8;color:#12334f;cursor:pointer;white-space:normal;line-height:1.3}
 .qp-lesson .qp-primary{background:#165c8a;color:#fff;border-color:#165c8a}
 /* WebKit's native menu label can extend the scrollable page beyond a narrow
    select. Keep native select semantics/keyboard behavior with a bounded face. */
 .qp-lesson select{display:block;width:100%;min-width:0;background:#fff;color:#162d40;appearance:none;overflow:hidden;text-overflow:ellipsis;padding-right:30px;
  background-image:linear-gradient(45deg,transparent 50%,#12334f 50%),linear-gradient(135deg,#12334f 50%,transparent 50%);
  background-position:calc(100% - 17px) 50%,calc(100% - 11px) 50%;background-size:6px 6px;background-repeat:no-repeat}
 .qp-lesson :disabled{opacity:.55;cursor:default}.qp-lesson :focus-visible{outline:3px solid #bc6300;outline-offset:2px}
 .qp-lesson .qp-actions{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
 .qp-lesson .qp-field{display:block;font:inherit;min-width:0;margin:10px 0}.qp-lesson .qp-field>span{display:block;font-weight:600;margin-bottom:4px}
 .qp-lesson fieldset{border:1px solid #bdcbd7;border-radius:6px;min-width:0;margin:12px 0;padding:8px 10px}
 .qp-lesson legend{font-weight:650;padding:0 4px}
 .qp-lesson summary{cursor:pointer;min-height:44px;padding:10px 0;font-weight:600}
 .qp-lesson .qp-note{font-size:.9em;color:#415b70}
 .qp-lesson .qp-conflict{padding:10px;background:#fff2ce;border-left:4px solid #936200}
 .qp-lesson [role=alert]{color:#92252a}
 .qp-lesson .qp-tree{list-style:none;padding:0;margin:10px 0;display:grid;gap:6px}
 .qp-lesson .qp-tree li{border-left:3px solid #3b779f;background:#f1f6fa;padding:8px}
 .qp-lesson .qp-tree small{display:block}
 .qp-lesson .qp-inspector{background:#f1f6fa;padding:10px;border-radius:5px}
 .qp-lesson dl{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:4px 10px;margin:6px 0}
 .qp-lesson dt{font-weight:600}.qp-lesson dd{margin:0}
 .qp-lesson .qp-error{padding:8px;background:#fff0eb}
 .qp-lesson .qp-summary{border-top:2px solid #4581a9;margin-top:12px;padding-top:8px}
 .qp-lesson.qp-overlay{border:1px solid #a7bac9;border-radius:0;padding:10px;line-height:1.25}
 .qp-overlay .qp-tree{margin:5px 0;gap:3px}.qp-overlay .qp-tree li{padding:4px 8px}
 .qp-overlay h3{margin:.3em 0}.qp-overlay p{margin:.25em 0}
 .qp-lesson .qp-private{border-top:1px solid #a7bac9;margin-top:10px}
 `));ctx.container.append(root);return root;
}
export function problem(item,language,compact=false){
 const w=words(language),root=el("div"),e=item.exercise;
 root.append(el("p",item.goal.kind==="best"?w.goalBest:w.goalBudget+" "+number(item.goal.max_cost,language)+"."));
 const context=details(w.context);
 const query=el("p");query.append(el("strong",w.query+": "));
 query.append(document.createTextNode(e.query.relations.map(r=>r.id+(r.filter?" ["+r.filter.column+" = "+JSON.stringify(r.filter.value)+"]":"")).join(", ")));
 for(const j of e.query.joins)query.append(document.createTextNode("; "+j.left.join(".")+" = "+j.right.join(".")));
 context.append(query,el("p",w.output+": "+e.query.output.map(c=>c.join(".")).join(", ")));
 for(const b of e.statistics.base) {
  const r=e.query.relations.find(r=>r.id===b.relation);
  context.append(el("p",b.relation+": "+w.rows+" "+number(b.rows,language)+", "+w.pages+" "+number(b.pages,language)+", "+w.width+" "+number(b.row_bytes,language)+(r.index?"; "+w.index+" "+r.index.column+" (h="+r.index.height+")":"; "+w.noIndex)));
 }
 for(const c of e.statistics.cardinalities)context.append(el("p",c.relations.join(" ⋈ ")+": "+number(c.rows,language)+" "+w.filtered.toLowerCase()));
 context.append(el("p",w.rules));
 root.append(context,el("p",w.hashLimit+": "+number(e.limits.hash_bytes,language)+" "+w.bytes,{class:"qp-note"}));
 if(!compact)root.append(el("p",w.units,{class:"qp-note"}));return root;
}
export function estimate(exercise,answer){try{return analyze(exercise,answer);}catch{return {valid:false,reason:"invalid-tree",node:-1};}}
export function feedback(own,w,language){
 if(!own)return w.empty;
 if(own.status==="pending")return w.pending;
 if(own.status==="unavailable")return w.unavailable;
 if(!own.feedback)return w.saved;
 const f=own.feedback;
 return (w[f.code]||w.saved)+(f.cost!==undefined?": "+number(f.cost,language):"")+(f.reason?". "+(w[f.reason]||w.invalid):"");
}
export function commandError(error,w){
 const code=error?.code||error?.receipt?.error;
 if(["stale-answer","stale-control","stale-epoch","stale-phase","stale-revision","concurrent-update","environment-changed"].includes(code))return w.stale;
 if(["closed","not-open","inactive","phase"].includes(code))return w.closedError;
 if(code==="reset-required")return w.stale;
 if(["session-capacity","capacity"].includes(code))return w.capacity;
 if(["queue-full","worker-timeout","worker-unavailable"].includes(code))return w.queue;
 return w.error;
}
// A receipt may arrive before its view. Never dispatch a second control with
// the previous version merely because the first promise resolved.
export function delivered(view,receipt){return !receipt || (view && (view.epoch>receipt.epoch || (view.epoch===receipt.epoch && view.revision>=receipt.revision)));}
