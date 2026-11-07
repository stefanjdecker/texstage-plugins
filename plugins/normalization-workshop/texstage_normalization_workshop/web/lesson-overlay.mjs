// SPDX-License-Identifier: Apache-2.0
import {words,el,shell,outline,fd} from "./lesson-ui.mjs";
import {discussionWords} from "./discussion-words.mjs";
import {answerCard} from "./analysis-view.mjs";
export function mount(ctx){
  const w=words(ctx.language),t=discussionWords(ctx.language),root=shell(ctx),label=el("h3"),
    context=el("p","R("+ctx.item.attributes.map(a=>a.id).join(", ")+"); F: "+
      (ctx.item.fds.map(p=>fd(p,ctx.item)).join("; ")||"∅")),cards=el("div",undefined,{class:"nw-comparison"});
  context.style.fontSize=".85em";root.append(label,context,cards);
  Object.assign(root.style,{position:"absolute",overflow:"auto",pointerEvents:"auto"});
  root.tabIndex=0;
  let placed=false,current,key="",width=0;
  function draw(){
    if(!current)return;const d=current,selected=ctx.role==="presenter"?d.selected:d.shared;
    const worked=d.phase==="revealed"?d.worked:null;
    root.hidden=!placed||!(selected.length||worked);
    cards.style.gridTemplateColumns=selected.length===2&&width>=760?"minmax(0,1fr) minmax(0,1fr)":"minmax(0,1fr)";
    const next=JSON.stringify([selected,worked,d.topic]);
    if(key===next)return;key=next;cards.replaceChildren();
    label.textContent=selected.length?(ctx.role==="presenter"?w.selected:w.shared)+(selected.length===2?" · "+t.comparison:""):w.worked;
    selected.forEach((row,i)=>cards.append(answerCard(ctx,row,w,(i===0?t.first:t.second)+" · v"+row.version,d.topic)));
    if(!selected.length&&worked){
      const content=el("section");content.append(el("p",outline(worked.answer,ctx.item).replaceAll("\n","; ")),el("p",worked.explanation));cards.append(content);
    }
  }
  return{
    place({box}){placed=Boolean(box);width=box?.w||0;if(box)Object.assign(root.style,{left:box.x+"px",top:box.y+"px",
      width:box.w+"px",height:box.h+"px",fontSize:Math.max(12,Math.min(19,box.w/48))+"px"});draw();},
    update({data}){current=data;draw();},destroy(){root.remove();}
  };
}
