// SPDX-License-Identifier: Apache-2.0
import {el,button,attrs,fd,outline} from "./lesson-ui.mjs";
import {discussionWords} from "./discussion-words.mjs";
import {chaseFrames,joinWitness,lostDependency,symbol} from "./evidence.mjs";
function table(item, rows, caption, t){
  const wrap=el("div",undefined,{class:"nw-table",tabindex:"0",role:"region","aria-label":caption});
  const grid=el("table"),head=el("tr");grid.append(el("caption",caption));
  head.append(el("th",t.row,{scope:"col"}));
  item.attributes.forEach(a=>head.append(el("th",a.id,{scope:"col"})));grid.append(head);
  rows.forEach((row,i)=>{const tr=el("tr");tr.append(el("th",String(i+1),{scope:"row"}));
    row.forEach((v,j)=>tr.append(el("td",symbol(v,j,item))));grid.append(tr);});
  wrap.append(grid);return wrap;
}
function tuple(values,item){return "("+values.map((v,j)=>symbol(v,j,item)).join(", ")+")";}
const attributeSet=(mask,item)=>mask?"{"+attrs(mask,item)+"}":"∅";
export function analysisPanel(ctx,answer,data,w,{topic="summary",phone=false}={}){
  const t=discussionWords(ctx.language),panel=el("section",undefined,{class:"nw-analysis"});
  if(!data){panel.append(el("p",t.noEvidence));return panel;}
  const f=data.facts,yn=v=>v===undefined?w.unknown:v?w.yes:w.no;
  if(data.mode==="classify"){
    panel.append(el("p",w.form+": "+f.normal_form.toUpperCase()),el("p",w.keys+": "+f.keys.map(k=>attributeSet(k,ctx.item)).join("; ")),
      el("p",answer.normal_form==="bcnf"?w.bcnf:f.witness_valid?t.correctWitness:t.wrongWitness));
    return panel;
  }
  panel.append(el("p",w.lossless+": "+yn(f.join?.lossless)+"; "+w.preserved+": "+yn(f.preservation?.preserved)),
    el("p",f.components.map(c=>"("+attrs(c.relation,ctx.item)+"): "+c.normal_form.toUpperCase()).join("; ")));
  if(!f.covered){panel.append(el("p",w.missing+": "+attrs(f.missing,ctx.item)),el("p",t.missing));return panel;}
  function joinProof(parent){
    const proof=joinWitness(ctx.item,answer,data);
    if(f.join.lossless){
      parent.append(el("p",t.losslessText),el("p",t.row+" "+(proof.row+1)+": "+tuple(proof.target,ctx.item)));
    }else{
      parent.append(el("p",t.legal),table(ctx.item,proof.table,w.lossless+": "+w.no,t),
        el("p",t.extra+": "+tuple(proof.target,ctx.item)),el("p",t.lossy));
      const projections=el("details"),list=el("ul");projections.append(el("summary",t.projection));
      proof.projections.forEach(p=>{
        const cols=ctx.item.attributes.map((_,i)=>i).filter(i=>p.relation&(1<<i));
        list.append(el("li","("+attrs(p.relation,ctx.item)+"): ("+
          p.values.map((v,i)=>symbol(v,cols[i],ctx.item)).join(", ")+") "+t.from+" "+(p.row+1)));
      });
      projections.append(list);parent.append(projections);
    }
    const trace=el("details",undefined,{class:"nw-trace"});trace.append(el("summary",t.trace));
    const frames=chaseFrames(ctx.item,answer,data),controls=el("div"),status=el("p","",{role:"status"}),area=el("div");
    let at=0;
    // Keep boundary controls focusable: native disabling can drop keyboard focus.
    const previous=button(t.previous,()=>{if(at>0){at--;draw();}}),
      next=button(t.next,()=>{if(at<frames.length-1){at++;draw();}}),
      final=button(t.final,()=>{if(at<frames.length-1){at=frames.length-1;draw();}});
    controls.append(previous,next,final);trace.append(el("p",t.construction),el("p",t.distinguished),controls,status,area);
    function draw(){
      previous.setAttribute("aria-disabled",String(at===0));
      for(const control of [next,final])control.setAttribute("aria-disabled",String(at===frames.length-1));
      const frame=frames[at],merge=frame.merge;
      status.textContent=t.step+" "+at+" / "+(frames.length-1)+": "+(merge?
        fd(ctx.item.fds[merge.fd],ctx.item)+"; "+t.row+" "+(merge.first+1)+", "+(merge.second+1)+". "+t.merge:t.initial);
      area.replaceChildren(table(ctx.item,frame.table,t.trace,t));
    }
    draw();parent.append(trace);
  }
  function preservationProof(parent){
    const proof=lostDependency(ctx.item,data);
    if(!proof){parent.append(el("p",t.preserved));return;}
    parent.append(el("p",w.lost+": "+fd(proof.dependency,ctx.item)),
      el("p",t.start+": "+attributeSet(proof.dependency[0],ctx.item)),
      el("p",t.closure+": "+attributeSet(proof.closure,ctx.item)+". "+t.outside),
      el("p",t.lostRows),table(ctx.item,proof.rows,w.lost,t),el("p",t.notOriginal));
  }
  if(phone){
    for(const [label,draw]of [[t.lossless,joinProof],[t.preservation,preservationProof]]){
      const details=el("details",undefined,{class:"nw-proof"});details.append(el("summary",label));draw(details);panel.append(details);
    }
  }else if(topic==="lossless")joinProof(panel);
  else if(topic==="preservation")preservationProof(panel);
  return panel;
}
export function answerCard(ctx,row,w,label,topic){
  const card=el("section",undefined,{class:"nw-comparison-card"});
  card.append(el("h3",label),el("p",outline(row.answer,ctx.item).replaceAll("\n","; ")));
  if(row.analysis)card.append(analysisPanel(ctx,row.answer,row.analysis,w,{topic}));
  return card;
}
