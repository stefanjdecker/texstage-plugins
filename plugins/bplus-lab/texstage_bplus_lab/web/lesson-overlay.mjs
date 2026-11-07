// SPDX-License-Identifier: Apache-2.0
import {key,preview,frameAt,focusIds} from "./editor-model.mjs";
import {words,local,el,shell,feedback,setText,taskText} from "./ui.mjs";
import {treeView} from "./tree-view.mjs";
import {answerView,stepLabel} from "./answer-view.mjs";
export function mount(ctx){
  const w=words(ctx.language),seed=ctx.item.exercise,root=shell(ctx,"bp-overlay");
  const heading=el("h3"),task=el("p",taskText(seed,w)),notice=el("p",undefined,{class:"bp-note"}),cursor=el("p",undefined,{class:"bp-badge"});
  const tree=treeView(ctx.language,ctx.signal,{presentation:true}),answerBox=el("div"),explanation=el("p"),status=el("p",undefined,{role:"status"});
  root.append(heading,task,notice,cursor,tree.root,answerBox,explanation,status);root.hidden=true;
  let placed=false,shown=false,alive=true,last="",generation=0;
  function visible(){root.hidden=!placed||!shown;}
  return {
    place(rects){
      const box=rects.box;placed=!!box;
      if(box)Object.assign(root.style,{left:box.x+"px",top:box.y+"px",width:box.w+"px",height:box.h+"px",
        fontSize:Math.max(12,Math.min(22,box.w/48))+"px"});
      visible();
    },
    update({data}){
      if(!alive)return;
      const source=data.replay?.source||(data.demonstration?"shared":"worked");
      const shownAnswer=source==="shared"?data.demonstration?.answer:data.worked?.answer;
      shown=!!shownAnswer;visible();
      const tokenKey=key([data.phase,source,shownAnswer,data.replay,data.demonstration?.feedback,data.worked]);
      if(last===tokenKey)return;last=tokenKey;const token=++generation;
      if(!shown)return;
      const focus=data.replay?.source===source?data.replay.focus:null;
      setText(heading,source==="shared"?w.shared:w.worked);
      setText(notice,source==="shared"&&data.phase!=="revealed"?w.predictionsOnly:"");
      notice.hidden=!notice.textContent;
      setText(cursor,focus?stepLabel(focus,w):w.prediction);
      answerBox.replaceChildren(answerView(shownAnswer,ctx.language,{focus:focus||{kind:"prediction"},compact:true}));
      setText(explanation,source==="worked"?local(data.worked.explanation,ctx.language):"");
      setText(status,source==="shared"&&data.demonstration.feedback?feedback({status:"saved",feedback:data.demonstration.feedback},w):"");
      tree.update(seed.tree,{highlight:focusIds(shownAnswer,focus)});
      // Never execute an unrevealed shared attempt: display its predictions.
      // Only revealed replay may show computed intermediate/final pages.
      if(data.phase!=="revealed")return;
      preview(seed,shownAnswer,{signal:ctx.signal,valid:()=>alive&&token===generation}).then(result=>{
        if(!result||!alive||token!==generation)return;
        const frame=frameAt(seed,result,focus||{kind:"prediction"});
        tree.update(frame.tree,{highlight:focusIds(shownAnswer,focus),pending:frame.pending});
      }).catch(()=>{if(alive&&token===generation)setText(status,w.unavailable);});
    },
    destroy(){alive=false;generation++;root.remove();}
  };
}
