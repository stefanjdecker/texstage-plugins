// SPDX-License-Identifier: Apache-2.0
import {words,el,shell,problem,local,number} from "./lesson-ui.mjs";
import {planView} from "./cost-inspector.mjs";
import {key} from "./plan-editor.mjs";
export function mount(ctx) {
 const w=words(ctx.language),root=shell(ctx,"qp-overlay"),title=el("h3"),explanation=el("p"),cost=el("p");
 const context=problem(ctx.item,ctx.language,true),viewer=planView(ctx.item.exercise,ctx.language,ctx.signal,{interactive:false});
 Object.assign(root.style,{position:"absolute",overflow:"auto",pointerEvents:"auto"});
 root.append(title,context,viewer.root,cost,explanation);root.hidden=true;
 let placed=false,shown=false,last="";
 function visible(){root.hidden=!placed||!shown;}
 return {
  place(rects){
   const box=rects.box;placed=!!box;
   if(box)Object.assign(root.style,{left:box.x+"px",top:box.y+"px",width:box.w+"px",height:box.h+"px",fontSize:Math.max(10,Math.min(22,box.w/43))+"px"});
   visible();
  },
  update({data}){
   // Presenter overlay mirrors the projector. Private references are confined
   // to its controls; ordinary exercise slides retain their prepared material.
   const solution=data.phase==="revealed"?data.solution:null;
   const plan=data.demonstration||solution?.worked_answer;
   shown=!!plan;visible();const next=key([plan,solution]);
   if(!shown||next===last)return;last=next;
   title.textContent=data.demonstration?w.shared:w.worked;viewer.update(plan);
   explanation.textContent=data.demonstration?"":local(solution?.explanation,ctx.language);
   cost.textContent=data.demonstration?"":w.minimum+": "+number(solution.minimum,ctx.language)+" · "+w.ties+": "+solution.ties;
  },
  destroy(){root.remove();}
 };
}
