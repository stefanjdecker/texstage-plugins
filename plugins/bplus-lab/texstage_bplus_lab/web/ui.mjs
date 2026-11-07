// SPDX-License-Identifier: Apache-2.0
export {words,local} from "./locale.mjs";
export function el(tag,text,attrs={}) {
  const node=document.createElement(tag);
  if(text!==undefined)node.textContent=text;
  for(const [k,v] of Object.entries(attrs))node.setAttribute(k,String(v));
  return node;
}
export function button(text,fn,signal,attrs={}) {
  const node=el("button",text,{type:"button",...attrs});node.addEventListener("click",fn,{signal});return node;
}
export function field(text,node,hint) {
  const label=el("label",undefined,{class:"bp-field"});label.append(el("span",text),node);
  if(hint)label.append(el("small",hint));return label;
}
export function option(value,label) {const n=el("option",label);n.value=String(value);return n;}
export function details(text) {const n=el("details");n.append(el("summary",text));return n;}
export function setText(node,text) {if(node.textContent!==text)node.textContent=text;}
export const delivered=(view,receipt)=>view&&receipt&&view.epoch===receipt.epoch&&view.revision>=receipt.revision;
export function feedback(own,w) {
  if(!own)return w.noAnswer;
  if(own.status==="pending")return w.pending;
  const f=own.feedback;if(!f)return w.saved;
  if(f.code==="unavailable")return w.unavailable;
  let text=(f.correct?w.correct:w.revise)+". "+(w.reason[f.reason]||"");
  if(f.failed?.length)text+=" "+w.failed+": "+f.failed.map(k=>w["claims"+k[0].toUpperCase()+k.slice(1)]).join(", ")+".";
  if(f.node!==undefined&&f.node!==null)text+=" "+w.page+" P"+f.node+".";
  return text;
}
const percent = value => String(value / 10) + "%";
const criteria = item => ["path","scan","keys","repairs","separators","height"]
  .filter(name => Object.hasOwn(item.rubric.weights,name)).map(name => [name,item.rubric.weights[name]]);
export function rubricView(item,w) {
  const box=details(w.rubric);box.dataset.bp="rubric";
  box.append(el("p",item.points ? item.points+" "+w.maximumPoints : w.practice));
  const table=el("table",undefined,{class:"bp-table"}),head=el("tr");
  head.append(el("th",w.criterion,{scope:"col"}),el("th",w.available,{scope:"col"}));table.append(head);
  for(const [name,weight] of criteria(item)){
    const row=el("tr");row.append(el("th",w.criteria[name],{scope:"row"}),el("td",percent(weight)));table.append(row);
  }
  box.append(table,el("p",w.rubricRules,{class:"bp-note"}),el("p",
    ["insert","delete"].includes(item.exercise.task.kind)?w.repairCredit:w.readCredit,{class:"bp-note"}));
  return box;
}
export function gradeView(grade,item,w) {
  const box=el("div",undefined,{"data-bp":"grade"});
  if(!grade)return box;
  box.append(el("p",w.savedGrade+": "+percent(grade.credit),{class:"bp-badge"}));
  const table=el("table",undefined,{class:"bp-table"}),head=el("tr");
  head.append(el("th",w.criterion,{scope:"col"}),el("th",w.earnedAvailable,{scope:"col"}));table.append(head);
  for(const [name,weight] of criteria(item)){
    const row=el("tr");row.append(el("th",w.criteria[name],{scope:"row"}),el("td",percent(grade.parts[name])+" / "+percent(weight)));table.append(row);
  }
  box.append(table);return box;
}
export function scoreView(own,scoring,item,w) {
  const box=el("section",undefined,{"data-bp":"score",class:"bp-card","aria-label":w.savedGrade});
  const status=!item.points?w.practice:!scoring?.released?w.pointsPrivate:
    scoring.awarded===null?w.ungraded:w.scoreboard+": "+scoring.awarded+" / "+scoring.maximum;
  box.append(el("p",status,{"data-bp":"awarded",role:"status"}),gradeView(own?.feedback?.grade,item,w));
  return box;
}
export function commandError(e,w) {
  if(["stale-answer","stale-phase","stale-control","stale-epoch","reset-required"].includes(e?.code))return w.stale;
  if(["closed","item-closed","inactive"].includes(e?.code))return w.closedError;
  if(["capacity","session-capacity"].includes(e?.code))return w.full;
  if(e?.code==="queue-full")return w.busy;
  if(e?.code==="invalid-answer")return w.invalid;
  return w.error;
}
export function taskText(seed,w) {
  const task=seed.task;
  return w[task.kind]+" "+(task.kind==="range"?"["+task.lower+", "+task.upper+"]":task.key);
}
export const style=`
.bp,.bp *{box-sizing:border-box}.bp[hidden],.bp [hidden]{display:none!important}
.bp{font:16px/1.45 system-ui,sans-serif;color:#18344a;background:#fbfcfe;border-radius:10px;padding:12px;min-width:0;max-width:100%;overflow-wrap:anywhere;text-align:left}
.bp h2,.bp h3,.bp h4{color:#18344a;line-height:1.2;margin:.55em 0}.bp h2{font-size:1.35em}.bp h3{font-size:1.15em}.bp h4{font-size:1em}
.bp p{margin:.5em 0;color:#18344a}.bp label,.bp legend{color:#18344a}.bp small,.bp .bp-note{font-size:.86em;color:#4c6172}.bp small{display:block}
.bp button,.bp input,.bp select{font:inherit;box-sizing:border-box;max-width:100%;min-width:0;border-radius:6px}
.bp button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;height:auto;padding:8px 12px;border:1px solid #7e94a4;background:#fff;color:#18344a;white-space:normal;cursor:pointer;line-height:1.25}
.bp button:disabled{opacity:.55;cursor:default}.bp button.bp-primary{background:#155a88;color:white;border-color:#155a88}
.bp :is(button,input,select,summary):focus-visible{outline:3px solid #c36a00;outline-offset:2px}
.bp input,.bp select{display:block;width:100%;min-height:44px;padding:8px;border:1px solid #7e94a4;background:#fff;color:#18344a}
.bp input[aria-invalid=true]{border:2px solid #ad361c}.bp input[type=range]{padding:0}
.bp fieldset{min-width:0;margin:10px 0;padding:10px;border:1px solid #c3d1db;border-radius:8px}.bp legend{font-weight:650;padding:0 4px}
.bp .bp-field{display:block;margin:8px 0}.bp .bp-field>span{display:block;font-weight:600;margin-bottom:3px}
.bp .bp-actions{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0}
.bp .bp-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:10px}
.bp .bp-card{border:1px solid #c3d1db;background:#fff;padding:10px;border-radius:8px;margin:10px 0}
.bp .bp-conflict{padding:10px;border:2px solid #b56d09;background:#fff6df;border-radius:8px}
.bp [role=alert]{color:#8e2519}.bp [role=status]{min-height:1em}
.bp .bp-private{border:2px dashed #6c4f95;padding:10px;background:#faf7ff;border-radius:8px}
.bp summary{cursor:pointer;min-height:44px;padding:10px 2px;font-weight:600}.bp details{margin:8px 0}
.bp .bp-pages{display:flex;flex-wrap:wrap;gap:5px}.bp .bp-pages button[aria-pressed=true]{border:2px solid #155a88;background:#e5f1fa}
.bp .bp-sequence{font-variant-numeric:tabular-nums;background:#eaf1f7;border-radius:6px;padding:8px;min-height:40px}
.bp .bp-overview{max-width:100%;overflow-x:auto;border:1px solid #d0dce6;background:#fff;border-radius:8px}
.bp svg{display:block;max-width:none}.bp .bp-table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
.bp .bp-table th,.bp .bp-table td{text-align:left;padding:5px;border-bottom:1px solid #d4dfe7;vertical-align:top}
.bp .bp-badge{padding:4px 8px;border-radius:5px;background:#e5f1fa;font-weight:600;display:inline-block}
.bp-controls{padding:2px 8px}.bp-controls>details{margin:0}.bp-controls .bp-panel{position:fixed;top:12px;left:12px;bottom:68px;width:min(780px,calc(100vw - 24px));overflow:auto;background:#fbfcfe;border:2px solid #52778f;border-radius:10px;padding:14px;box-shadow:0 6px 30px #001d3b55;z-index:100}
.bp-overlay{position:absolute;overflow:auto;pointer-events:auto;border:1px solid #c3d1db;font-size:clamp(12px,1.3vw,22px)}
.bp-overlay .bp-overview svg{max-width:100%;height:auto}.bp-overlay .bp-card{margin:4px 0}.bp-overlay h3{margin:.2em 0}.bp-overlay p{margin:.3em 0}.bp-overlay .bp-table th,.bp-overlay .bp-table td{padding:3px}
@media(max-width:380px){.bp{padding:8px}.bp button{padding:8px}.bp .bp-actions>*{flex:1 1 auto}.bp-controls .bp-panel{left:6px;width:calc(100vw - 12px);padding:8px}}
@media(prefers-reduced-motion:reduce){.bp *{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
`;
export function shell(ctx,kind) {
  const root=el("section",undefined,{class:"bp "+kind,lang:String(ctx.language).startsWith("de")?"de":"en"});
  root.append(el("style",style));ctx.container.append(root);return root;
}
