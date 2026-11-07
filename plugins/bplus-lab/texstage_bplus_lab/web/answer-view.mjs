// SPDX-License-Identifier: Apache-2.0
import {el,words} from "./ui.mjs";
export function answerView(answer,language,{focus=null,compact=false}={}) {
  const w=words(language),root=el("div",undefined,{class:"bp-answer"});
  const line=(name,text)=>{const p=el("p");p.append(el("strong",name+": "),document.createTextNode(text));root.append(p);};
  if(compact&&focus?.kind==="start")return root;
  if(!compact||focus?.kind==="path")line(w.path,(compact?answer.path.slice(0,focus.index+1):answer.path).map(n=>"P"+n).join(" → ")||w.empty);
  if(answer.leaves&&(!compact||focus?.kind==="scan"))line(w.leaves,(compact?answer.leaves.slice(0,focus.index+1):answer.leaves).map(n=>"P"+n).join(" → "));
  if(answer.keys&&(!compact||focus?.kind==="prediction"))line(w.returned,answer.keys.join(", ")||"∅");
  if(answer.repairs&&(!compact||["repair","prediction"].includes(focus?.kind))){
    const list=el("ol");
    answer.repairs.forEach((r,i)=>{
      if(compact&&(focus.kind!=="repair"||focus.index!==i))return;
      const text=w[r.op]+" P"+r.node+(r.op==="split"?
        " · "+w.leftCount+": "+r.left_count+" · "+w.separator+": "+r.separator:" · "+w.sibling+": P"+r.sibling);
      const li=el("li",text);if(focus?.kind==="repair"&&focus.index===i)li.className="bp-badge";list.append(li);
    });
    if(!compact||focus.kind==="repair")root.append(el("strong",w.repairs),answer.repairs.length?list:el("p",w.none));
    if(compact&&focus.kind!=="prediction")return root;
    const table=el("table",undefined,{class:"bp-table"}),head=el("thead"),tr=el("tr");
    tr.append(el("th",w.page,{scope:"col"}),el("th",w.keys,{scope:"col"}));head.append(tr);table.append(head);
    const body=el("tbody");
    for(const row of answer.separators){const tr=el("tr");tr.append(el("th","P"+row.node,{scope:"row"}),el("td",row.keys.join(", ")));body.append(tr);}
    table.append(body);root.append(el("strong",w.separators),answer.separators.length?table:el("p",w.none));line(w.height,String(answer.height));
  }
  return root;
}
export function stepLabel(focus,w){
  const label={start:w.start,prediction:w.prediction,path:w.pathStep,scan:w.scanStep,repair:w.repairStep}[focus?.kind]||w.start;
  return label+(Number.isInteger(focus?.index)?" "+(focus.index+1):"");
}
