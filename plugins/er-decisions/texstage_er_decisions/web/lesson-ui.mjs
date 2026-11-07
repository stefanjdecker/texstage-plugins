// SPDX-License-Identifier: Apache-2.0
export const local = (v, language) => v?.[language?.startsWith("de") ? "de" : "en"] || "";
export const words = language => {
  const de = language?.startsWith("de");
  const pairs = {
    requirements:["Fixed requirements","Feste Anforderungen"], example:["Permitted example","Erlaubtes Beispiel"],
    decisions:["Your decisions","Ihre Entscheidungen"], model:["View model","Modell ansehen"], back:["Back to decisions","Zurück zu den Entscheidungen"],
    preview:["Your model preview","Ihre Modellvorschau"], undecided:["Not chosen yet","Noch nicht gewählt"],
    help:["Choose one option in each card. In the bounds, * means any number. Previewing does not submit your answer.","Wählen Sie pro Karte eine Option. Bei den Grenzen bedeutet * eine beliebige Anzahl. Die Vorschau sendet keine Antwort."],
    rationale:["Reason for your choices (optional)","Begründung Ihrer Entscheidungen (optional)"],
    sharing:["Your teacher can inspect your answer and reason. Sharing a reason with the class requires a separate teacher action.","Die Lehrperson kann Antwort und Begründung ansehen. Eine Begründung wird nur durch eine gesonderte Freigabe mit der Klasse geteilt."],
    save:["Save answer","Antwort speichern"], draft:["Draft; not saved yet.","Entwurf; noch nicht gespeichert."],
    saved:["Answer saved. Feedback follows when the teacher reveals it.","Antwort gespeichert. Rückmeldung folgt bei der Auflösung."],
    pending:["Saved; waiting for the presenter's computer.","Gespeichert; wartet auf den Präsentationsrechner."],
    unavailable:["Evaluation is unavailable. Your answer remains saved.","Die Auswertung ist nicht verfügbar. Ihre Antwort bleibt gespeichert."],
    checked:["This model passes the configured examples.","Dieses Modell besteht die konfigurierten Beispiele."],
    contradiction:["This model conflicts with the configured examples. Compare the alternatives below, then repair your choices when answers reopen.","Dieses Modell widerspricht den konfigurierten Beispielen. Vergleichen Sie die Alternativen und ändern Sie Ihre Entscheidungen, sobald Antworten wieder geöffnet sind."],
    finite:["These finite examples support the discussion; passing them is not a proof for every possible database.","Diese endlichen Beispiele unterstützen die Diskussion; sie sind kein Beweis für jede mögliche Datenbank."],
    reload:["Reload saved answer","Gespeicherte Antwort laden"], keep:["Keep my draft","Meinen Entwurf behalten"],
    conflict:["The saved answer or activity has changed. Reload it or keep your draft explicitly. Neither action submits an answer.","Die gespeicherte Antwort oder Aktivität hat sich geändert. Laden Sie sie neu oder behalten Sie Ihren Entwurf ausdrücklich. Beides sendet keine Antwort."],
    incomplete:["Choose one option in every card before saving.","Wählen Sie vor dem Speichern eine Option in jeder Karte."],
    badRationale:["Use a shorter plain-text reason (up to 160 characters; long Unicode text may need further shortening).","Verwenden Sie eine kürzere Begründung (höchstens 160 Zeichen; langer Unicode-Text muss eventuell weiter gekürzt werden)."],
    openButton:["Open answers","Antworten öffnen"], closeButton:["Close answers","Antworten schließen"],
    reveal:["Reveal alternatives","Alternativen auflösen"], reset:["Reset activity","Aktivität zurücksetzen"],
    resetConfirm:["Reset all answers in this activity?","Alle Antworten in dieser Aktivität zurücksetzen?"],
    scoredReset:["Reset all answers and remove the points awarded by this activity?","Alle Antworten zurücksetzen und die Punkte dieser Aktivität entfernen?"],
    scoredRound:["This scored round is closed. Reset the activity to start another round; this removes its previous points.","Diese bewertete Runde ist abgeschlossen. Setzen Sie die Aktivität für eine neue Runde zurück; dabei werden ihre bisherigen Punkte entfernt."],
    scoredContradiction:["This model conflicts with the configured examples. Compare the alternatives below. This scored round is closed.","Dieses Modell widerspricht den konfigurierten Beispielen. Vergleichen Sie die Alternativen. Diese bewertete Runde ist abgeschlossen."],
    pointsLabel:["Activity points","Aktivitätspunkte"],
    pointsRule:["points for a fully correct model, awarded on reveal. No speed bonus.","Punkte für ein vollständig korrektes Modell, vergeben bei der Auflösung. Kein Zeitbonus."],
    introduce:["Introduction","Einführung"], open:["Open","Offen"], closed:["Closed","Geschlossen"], revealed:["Revealed","Aufgelöst"],
    phase:["Phase","Phase"], count:["Answers","Antworten"], none:["No selection","Keine Auswahl"],
    inspect:["Inspect an answer privately","Antwort privat ansehen"], response:["Answer","Antwort"],
    share:["Share selected answer anonymously","Ausgewählte Antwort anonym teilen"], clear:["Clear shared answer","Geteilte Antwort entfernen"],
    include:["Also share the reason with the class","Auch die Begründung mit der Klasse teilen"],
    shared:["Anonymously shared model","Anonym geteiltes Modell"], selected:["Private inspection","Private Ansicht"],
    counts:["Checks: pending / passed / not passed / unavailable","Prüfungen: ausstehend / bestanden / nicht bestanden / nicht verfügbar"],
    options:["Choices across saved answers","Entscheidungen der gespeicherten Antworten"],
    previous:["Previous answers","Vorherige Antworten"], next:["Next answers","Nächste Antworten"],
    page:["Page","Seite"], worked:["Checked alternatives","Geprüfte Alternativen"], counterexamples:["Why a model can fail","Warum ein Modell scheitern kann"],
    constraints:["Constraints in words","Bedingungen in Worten"], bounds:["Links per","Verknüpfungen pro"],
    owner:["Where does this attribute belong?","Wohin gehört dieses Attribut?"], representation:["Representation of","Darstellung von"],
    relationship:["Relationship","Beziehung"], entity:["Association entity","Assoziationsentität"],
    unique:["Each pair occurs at most once.","Jedes Paar kommt höchstens einmal vor."],
    duplicates:["Different IDs may represent the same pair.","Verschiedene IDs dürfen dasselbe Paar repräsentieren."],
    error:["The command failed. Your draft is preserved; retry when ready.","Der Befehl ist fehlgeschlagen. Ihr Entwurf bleibt erhalten; versuchen Sie es erneut."],
    stale:["The state changed. Check the current view and retry.","Der Stand hat sich geändert. Prüfen Sie die aktuelle Ansicht und versuchen Sie es erneut."],
    closedError:["Answers are currently closed.","Antworten sind momentan geschlossen."],
    capacity:["Capacity has been reached. Your saved answer is preserved.","Die Kapazität ist erreicht. Ihre gespeicherte Antwort bleibt erhalten."],
    queue:["Evaluation is busy. Please retry.","Die Auswertung ist ausgelastet. Bitte versuchen Sie es erneut."],
  };
  return {...Object.fromEntries(Object.entries(pairs).map(([k,v])=>[k,v[de ? 1 : 0]])),de:!!de};
};
export function el(tag, text, attrs={}) {
  const n=document.createElement(tag);
  if (text !== undefined) n.textContent=text;
  for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,v);
  return n;
}
let nextId=0;
export function uniqueId(){
  let id;do{id="texstage-er-"+(++nextId);}while(document.getElementById(id));
  return id;
}
// Repeated view pushes must not re-announce an unchanged live-region message.
export function setText(node,text){if(node.textContent!==text)node.textContent=text;}
export function button(text, action, signal) {
  const b=el("button",text,{type:"button"}); b.addEventListener("click",action,{signal}); return b;
}
export function shell(ctx) {
  const root=el("section",undefined,{class:"er-lesson",lang:ctx.language?.startsWith("de")?"de":"en",
    "aria-label":local(ctx.item.title,ctx.language)||words(ctx.language).decisions});
  root.append(el("style",`
.er-lesson{box-sizing:border-box;min-width:0;max-width:100%;padding:14px;background:#fff;color:#192d3b;font:16px/1.45 system-ui,sans-serif;overflow-wrap:anywhere}
.er-lesson *{box-sizing:border-box}.er-lesson [hidden]{display:none!important}
.er-lesson h2{font-size:1.2em;margin:0 0 .6em}.er-lesson h3{font-size:1.05em;margin:.7em 0 .4em}.er-lesson p{margin:.5em 0}
.er-lesson button,.er-lesson select,.er-lesson summary{font:inherit;min-height:44px;max-width:100%;padding:8px;white-space:normal}
.er-lesson button{border:1px solid #667c8c;border-radius:6px;background:#edf4fa;color:#183c59;margin:4px 6px 4px 0;cursor:pointer}
.er-lesson button[data-primary]{background:#174f73;color:white}.er-lesson :disabled{opacity:.55;cursor:default}
.er-lesson :focus-visible{outline:3px solid #ac4d00;outline-offset:3px}
.er-lesson fieldset{min-width:0;margin:12px 0;padding:10px;border:1px solid #acbdc8;border-radius:8px}
.er-lesson legend{font-weight:650;padding:0 6px;max-width:100%}
.er-lesson .er-option{display:flex;align-items:flex-start;gap:8px;min-height:44px;padding:10px 6px;cursor:pointer;border-radius:4px}
.er-lesson .er-option:has(input:checked){background:#e4f1fa}.er-lesson input[type=radio],.er-lesson input[type=checkbox]{flex:none;width:20px;height:20px;margin:2px 0;accent-color:#174f73}
.er-lesson textarea{display:block;width:100%;min-height:90px;font:inherit;padding:8px;border:1px solid #667c8c;border-radius:4px;resize:vertical}
.er-lesson .er-muted{color:#42596b;font-size:.9em}.er-lesson .er-conflict{padding:12px;border-left:4px solid #ab6500;background:#fff2cd}
.er-lesson [role=alert]{color:#9a2230}.er-lesson ul{padding-left:1.3em}.er-lesson li{margin:.3em 0}
.er-lesson .er-diagram{display:flex;align-items:center;gap:4px;margin:12px 0}
.er-lesson .er-node{flex:1;min-width:0;text-align:center;border:2px solid #527189;border-radius:5px;background:#eef5fa;padding:8px 5px}
.er-lesson .er-relation{border-style:dashed;background:#fff4dd}.er-lesson .er-association{border-style:double;border-width:4px;background:#edf7ed}
.er-lesson .er-node small{display:block;font-size:.75em}.er-lesson .er-link{flex:none;color:#527189}
.er-lesson .er-model{margin:.5em 0}.er-lesson .er-model ul{font-size:.9em}
.er-lesson details{border-top:1px solid #cfdae1;margin-top:10px}.er-lesson summary{cursor:pointer;font-weight:600}
.er-lesson .er-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:12px}
.er-lesson .er-card{padding:10px;background:#f5f8fa;border:1px solid #c6d3dd;border-radius:7px}
.er-lesson .er-records{font-size:.9em;white-space:pre-wrap;margin:.4em 0;overflow-wrap:anywhere}
.er-lesson.er-overlay{padding:8px}.er-lesson.er-overlay .er-grid{grid-template-columns:1fr 1fr;gap:8px}
.er-lesson.er-overlay .er-card{padding:6px}.er-lesson.er-overlay p{margin:.2em 0}.er-lesson.er-overlay h3{margin:.2em 0}
.er-lesson.er-overlay .er-diagram{margin:5px 0}.er-lesson.er-overlay li{margin:.15em 0}
@media(max-width:420px){.er-lesson{padding:10px}.er-lesson .er-diagram{flex-direction:column}.er-lesson .er-node{width:100%}.er-lesson .er-link{transform:rotate(90deg)}}
`));
  ctx.container.append(root); return root;
}
export function feedback(own,w,points=0) {
  if (!own) return "";
  if(points&&own.feedback?.code==="contradiction")return w.scoredContradiction;
  if (own.feedback) return w[own.feedback.code] || w.unavailable;
  return own.status==="pending" ? w.pending : own.status==="unavailable" ? w.unavailable : w.saved;
}
export function errorText(e,w) {
  if (["stale-answer","stale-control","stale-epoch","stale-phase"].includes(e?.code)) return w.stale;
  if (["capacity","session-capacity"].includes(e?.code)) return w.capacity;
  if (["queue-full","worker-unavailable","worker-timeout"].includes(e?.code)) return w.queue;
  if (["closed","phase","inactive"].includes(e?.code)) return w.closedError;
  if (e?.code==="invalid-rationale") return w.badRationale;
  if (e?.code==="reset-required") return w.scoredRound;
  return w.error;
}
export function names(item,language) {
  return {entities:Object.fromEntries(item.labels.entities.map(r=>[r.id,local(r.text,language)])),
    relationship:local(item.labels.relationship,language),
    attributes:Object.fromEntries(item.labels.attributes.map(r=>[r.id,local(r.text,language)]))};
}
export function bounds(value) { return value.min==null ? "?" : value.min+".."+(value.max==="many"?"*":value.max); }
export function decisionText(item,d,language) {
  const w=words(language), n=names(item,language), roles=item.model.relationship.roles;
  const roleName=id=>n.entities[roles.find(r=>r.id===id).entity];
  if (d.kind==="role-bounds") return {title:w.bounds+" "+roleName(d.target), options:d.options.map(o=>({
    id:o.id,text:bounds(o.value)+(w.de?" Verknüpfungen":" links"),
    detail:w.de ? "Für jede einzelne Entität: "+roleName(d.target)+"." : "For each individual "+roleName(d.target)+"."
  }))};
  if (d.kind==="attribute-owner") return {title:n.attributes[d.target]+": "+w.owner,options:d.options.map(o=>({
    id:o.id,text:o.value==="relationship"?n.relationship:roleName(o.value),
    detail:w.de ? "Ein Wert pro "+(o.value==="relationship"?n.relationship:roleName(o.value))+"." :
      "One value per "+(o.value==="relationship"?n.relationship:roleName(o.value))+"."
  }))};
  return {title:w.representation+" "+n.relationship,options:d.options.map(o=>({
    id:o.id,text:o.value.form==="relationship"?w.relationship:w.entity,
    detail:o.value.pair_unique?w.unique:w.duplicates
  }))};
}
export function records(item,snapshot,language) {
  const n=names(item,language), roles=item.model.relationship.roles;
  return snapshot.entities.map(e=>n.entities[e.entity]+": "+(e.ids.join(", ")||"∅")).join(" · ")+"\n"+
    snapshot.links.map(link=>link.id+": "+link.roles.map(([id,value])=>
      n.entities[roles.find(r=>r.id===id).entity]+"="+value).concat(link.values.map(([id,value])=>n.attributes[id]+"="+value)).join(", ")).join("\n");
}
export function publicMaterial(ctx,root,w) {
  root.append(el("h2",local(ctx.item.title,ctx.language)),el("p",local(ctx.item.brief,ctx.language)));
  if(ctx.item.points)root.append(el("p",ctx.item.points+" "+w.pointsRule,{class:"er-points-rule"}));
  const details=el("details"), list=el("ul");
  details.append(el("summary",w.requirements)); details.open=true;
  for (const r of ctx.item.requirements) list.append(el("li",local(r.text,ctx.language)));
  details.append(list); root.append(details);
  const example=el("details"); example.append(el("summary",w.example),
    el("p",records(ctx.item,ctx.item.examples[0],ctx.language),{class:"er-records"})); root.append(example);
}

