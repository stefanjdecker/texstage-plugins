// SPDX-License-Identifier: Apache-2.0
import {el,decisionText,uniqueId} from "./lesson-ui.mjs";
export function decisionEditor(ctx,parent,changed) {
  const inputs=[],cards=[];
  for (const [index,d] of ctx.item.decisions.entries()) {
    const text=decisionText(ctx.item,d,ctx.language), card=el("fieldset",undefined,{"data-decision":d.id});
    card.append(el("legend",(index+1)+". "+text.title));
    const name=uniqueId(),members=[];cards.push({card,members});
    for (const option of text.options) {
      const label=el("label",undefined,{class:"er-option"});
      const input=el("input",undefined,{type:"radio",name,value:option.id,"data-choice":d.id+":"+option.id});
      const content=el("span",option.text);content.append(el("small",option.detail,{class:"er-muted",style:"display:block"}));
      label.append(input,content);card.append(label);inputs.push({input,decision:d.id});members.push(input);
      input.addEventListener("change",changed,{signal:ctx.signal});
    }
    parent.append(card);
  }
  return {
    get:()=>inputs.filter(r=>r.input.checked).map(r=>[r.decision,r.input.value]).sort(([a],[b])=>a<b?-1:a>b?1:0),
    set(choices) { const selected=new Map(choices);for(const r of inputs)r.input.checked=selected.get(r.decision)===r.input.value; },
    clearValidation(){
      for(const {card,members} of cards)for(const node of [card,...members]){
        node.removeAttribute("aria-invalid");node.removeAttribute("aria-describedby");
      }
    },
    validate(errorId){
      let first=null;
      for(const {card,members} of cards)if(!members.some(n=>n.checked)){
        first||=members[0];
        for(const node of [card,...members]){
          node.setAttribute("aria-invalid","true");node.setAttribute("aria-describedby",errorId);
        }
      }
      return first;
    },
    focus(){ inputs[0]?.input.focus(); }
  };
}

