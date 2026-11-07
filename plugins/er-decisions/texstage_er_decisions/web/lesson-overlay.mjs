// SPDX-License-Identifier: Apache-2.0
import {el,shell,words} from "./lesson-ui.mjs";
import {modelView} from "./diagram.mjs";
import {teachingView} from "./teaching.mjs";
export function mount(ctx){
  const w=words(ctx.language),root=shell(ctx);root.classList.add("er-overlay");
  Object.assign(root.style,{position:"absolute",overflow:"auto",pointerEvents:"auto"});
  root.setAttribute("tabindex","0");root.setAttribute("aria-label",w.worked);
  const body=el("div");root.append(body);let placed=false,key;
  function fit(){
    if(root.hidden)return;
    let size=parseFloat(root.style.fontSize);
    for(let i=0;i<24&&size>10&&(root.scrollHeight>root.clientHeight+1||root.scrollWidth>root.clientWidth+1);i++){
      size=Math.max(10,size*.95);root.style.fontSize=size+"px";
    }
  }
  return {
    place(rects){
      const box=rects.box;placed=!!box;
      if(!box){root.hidden=true;return;}
      Object.assign(root.style,{left:box.x+"px",top:box.y+"px",width:box.w+"px",height:box.h+"px",
        fontSize:Math.max(10,Math.min(22,box.h/28,box.w/65))+"px"});
      fit();
    },
    update({data}){
      // Private selection never replaces the projected exercise.
      const teaching=data.phase==="revealed"?data.teaching:null,shared=data.demonstration;
      root.setAttribute("aria-label",shared?w.shared:w.worked);
      root.hidden=!placed||(!shared&&!teaching);
      const next=JSON.stringify([shared,teaching]);
      if(key===next){fit();return;}key=next;body.replaceChildren();
      if(shared){
        body.append(el("h3",w.shared),modelView(ctx.item,shared.model,ctx.language));
        if(shared.rationale)body.append(el("p",shared.rationale));
      }else if(teaching)body.append(teachingView(ctx,teaching,{compact:true}));
      fit();
    },
    destroy(){root.remove();}
  };
}

