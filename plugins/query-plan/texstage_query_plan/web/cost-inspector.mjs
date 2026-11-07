// SPDX-License-Identifier: Apache-2.0
import {el,field,option,words,number,estimate} from "./lesson-ui.mjs";
export function nodeName(n,i,w) {
 return w.node+" "+(i+1)+": "+(n.op==="scan"?n.relation+" — "+w[n.method]:
   w[n.method==="nested"?"nested":"hash"]+" ("+(n.left+1)+" + "+(n.right+1)+")"+(n.method==="nested"?"":"; "+w.build.toLowerCase()+" "+w[n.method==="hash-left"?"left":"right"].toLowerCase()));
}
export function arithmetic(exercise,answer,result,i,language) {
 const w=words(language),n=answer.nodes[i],f=result.nodes[i],num=x=>number(x,language);
 let formula,memory="";
 if(n.op==="scan"){
  const b=exercise.statistics.base.find(b=>b.relation===n.relation),r=exercise.query.relations.find(r=>r.id===n.relation);
  formula=n.method==="seq"?"100 × "+num(b.pages)+" + "+num(b.rows):"400 × ("+r.index.height+" + "+num(f.rows)+") + "+num(f.rows);
 }else{
  const a=result.nodes[n.left],b=result.nodes[n.right];
  if(n.method==="nested")formula=num(a.rows)+" × "+num(b.rows)+" + "+num(f.rows);
  else{
   const [build,probe]=n.method==="hash-left"?[a,b]:[b,a];
   formula="2 × "+num(build.rows)+" + "+num(probe.rows)+" + "+num(f.rows);
   memory=num(build.rows)+" × ("+num(build.row_bytes)+" + 16) = "+num(f.hash_bytes)+" "+w.bytes+" ≤ "+num(exercise.limits.hash_bytes);
  }
  formula+=" = "+num(f.local_cost)+"; "+w.totalCost+": "+num(a.total_cost)+" + "+num(b.total_cost)+" + "+num(f.local_cost);
 }
 return {formula:formula+" = "+num(f.total_cost),memory};
}
export function planView(exercise,language,signal,{interactive=true}={}) {
 const w=words(language),root=el("div"),list=el("ol",undefined,{class:"qp-tree","aria-label":w.tree});
 const pick=el("select",undefined,{"aria-label":w.inspectNode}),inspect=el("div",undefined,{class:"qp-inspector"});
 const choice=field(w.inspectNode,pick);let answer,result,chosen=0;
 function detail(){
  inspect.replaceChildren();
  if(!result?.valid)return;
  const f=result.nodes[chosen],n=answer.nodes[chosen],a=arithmetic(exercise,answer,result,chosen,language);
  inspect.append(el("strong",nodeName(n,chosen,w)));
  const dl=el("dl");
  for(const [name,value]of[[w.filtered,f.rows],[w.width,f.row_bytes],[w.localCost,f.local_cost],[w.totalCost,f.total_cost],[w.workspace,f.hash_bytes]]){
   dl.append(el("dt",name),el("dd",number(value,language)));
  }
  inspect.append(dl,el("p",w.arithmetic+": "+a.formula));if(a.memory)inspect.append(el("p",a.memory));
 }
 pick.addEventListener("change",()=>{chosen=Number(pick.value);detail();},{signal});
 root.append(list,choice,inspect);
 return {root,update(plan,analysis){
  answer=plan;result=analysis||estimate(exercise,plan);list.replaceChildren();
  if(!plan||!result.valid){
   list.append(el("li",(w[result?.reason]||w.invalid)+(result?.node>=0?" ("+w.node+" "+(result.node+1)+")":"")));
   choice.hidden=inspect.hidden=true;return;
  }
  const sequence=[];function visit(i,depth){sequence.push([i,depth]);const n=plan.nodes[i];if(n.op==="join"){visit(n.left,depth+1);visit(n.right,depth+1);}}
  visit(plan.nodes.length-1,0);
  for(const [i,depth]of sequence){
   const n=plan.nodes[i],f=result.nodes[i],row=el("li");row.style.marginLeft=depth*.6+"em";
   row.append(el("strong",nodeName(n,i,w)),el("small",w.filtered+": "+number(f.rows,language)+" · "+w.localCost+": "+number(f.local_cost,language)+" · "+w.totalCost+": "+number(f.total_cost,language)));
   list.append(row);
  }
  const value=String(Math.min(chosen,plan.nodes.length-1));
  const wanted=plan.nodes.map((n,i)=>nodeName(n,i,w));
  if(JSON.stringify([...pick.options].map(o=>o.textContent))!==JSON.stringify(wanted))pick.replaceChildren(...wanted.map((name,i)=>option(String(i),name)));
  pick.value=value;chosen=Number(value);
  choice.hidden=inspect.hidden=!interactive; if(interactive)detail();
 }};
}
