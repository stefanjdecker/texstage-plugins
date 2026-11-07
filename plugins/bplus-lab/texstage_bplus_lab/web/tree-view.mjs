// SPDX-License-Identifier: Apache-2.0
import {el,field,option,button,details,words} from "./ui.mjs";

import {key} from "./editor-model.mjs";
const NS="http://www.w3.org/2000/svg";
let sequence=0;
function svg(tag,attrs={},text) {
  const n=document.createElementNS(NS,tag);
  for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));
  if(text!==undefined)n.textContent=text;return n;
}
export function geometry(tree) {
  const nodes=new Map(tree.nodes.map(n=>[n.id,n])),positions=new Map(),depths=new Map();
  let cursor=16,deepest=0;
  function place(id,depth) {
    const node=nodes.get(id);if(!node||depth>4||positions.has(id))return;
    const width=Math.max(180,36+node.keys.length*52);
    deepest=Math.max(deepest,depth);depths.set(id,depth);
    if(node.kind==="leaf"){positions.set(id,{x:cursor,y:20+depth*118,w:width,h:68});cursor+=width+26;}
    else{
      node.children.forEach(child=>place(child,depth+1));
      const first=positions.get(node.children[0]),last=positions.get(node.children.at(-1));
      positions.set(id,{x:(first.x+first.w/2+last.x+last.w/2)/2-width/2,y:20+depth*118,w:width,h:68});
    }
  }
  place(tree.root,0);
  const min=Math.min(0,...[...positions.values()].map(p=>p.x-12));
  for(const p of positions.values())p.x-=min;
  return {positions,depths,width:Math.max(320,cursor-min+12),height:Math.max(120,deepest*118+115)};
}
export function treeView(language,signal,{interactive=false,onFocus=()=>{},focusTag="focus",presentation=false}={}) {
  const w=words(language),root=el("div",undefined,{class:"bp-tree"}),frame=el("div",undefined,{class:"bp-overview",tabindex:"0","aria-label":w.tree});
  const legend=el("p",w.legend,{class:"bp-note"}),picker=el("select",undefined,{"data-bp":focusTag});
  const card=el("div",undefined,{class:"bp-card","data-bp":"focused-page"}),outline=details(w.outline),pageList=el("div",undefined,{class:"bp-pages"});
  const overview=details(w.tree);
  const id="bp-arrow-"+(++sequence);
  let current=null,focused=null,previous="";
  function nodeText(n){return "P"+n.id+" · "+(n.kind==="leaf"?w.leaf:w.internal)+" · "+(n.keys.join(", ")||w.empty);}
  function focus(value,notify=true) {
    focused=Number(value);picker.value=String(focused);paintFocus();
    if(notify)onFocus(focused);
  }
  picker.addEventListener("change",()=>focus(picker.value),{signal});
  function paintFocus(){
    if(!current)return;
    const restore=card.contains(document.activeElement);
    const n=current.nodes.find(n=>n.id===focused)||current.nodes[0];focused=n.id;
    card.replaceChildren(el("strong","P"+n.id+" · "+(n.id===current.root?w.root+" · ":"")+(n.kind==="leaf"?w.leaf:w.internal)),
      el("p",(n.kind==="leaf"?w.entries:w.separators)+": "+(n.keys.join(", ")||w.empty)));
    const links=el("div",undefined,{class:"bp-actions"});
    if(n.kind==="internal"){
      card.append(el("p",w.children));
      for(const child of n.children)links.append(button("P"+child,()=>focus(child),signal,{"aria-label":w.focus+" P"+child}));
    }else{
      card.append(el("p",w.nextLeaf+": "+(n.next===null?w.none:"P"+n.next)));
      if(n.next!==null)links.append(button(w.follow+" · P"+n.next,()=>focus(n.next),signal));
    }
    card.append(links);
    const parent=current.nodes.find(p=>p.children?.includes(n.id));
    const siblings=parent?.children.filter(id=>id!==n.id)||[];
    card.append(el("p",w.siblings+": "+(siblings.map(n=>"P"+n).join(", ")||w.none),{class:"bp-note"}));
    for(const b of pageList.querySelectorAll("button"))b.setAttribute("aria-pressed",String(Number(b.dataset.page)===focused));
    if(restore)picker.focus();
  }
  if(interactive){
    outline.append(pageList);overview.append(el("p",w.scrollHint,{class:"bp-note"}),frame);
    root.append(field(w.focus,picker),card,overview,outline,legend);
  }else root.append(frame,legend);
  return {
    root,
    get focused(){return focused;},
    focus,
    update(tree,{highlight=[],pending=null}={}){
      current=tree;const token=key([tree,highlight,pending]);
      if(token===previous)return;previous=token;
      if(interactive){
        const old=focused;picker.replaceChildren(...tree.nodes.map(n=>option(n.id,nodeText(n))));
        pageList.replaceChildren(...tree.nodes.map(n=>button(nodeText(n),()=>focus(n.id),signal,{"data-page":n.id,"aria-pressed":"false"})));
        focus(tree.nodes.some(n=>n.id===old)?old:tree.root,false);
      }
      const g=geometry(tree),zoom=presentation&&g.width>1250;
      const focusNode=tree.nodes.find(n=>n.id===(pending??highlight.at(-1)))||tree.nodes.find(n=>n.id===tree.root);
      const at=g.positions.get(focusNode.id),vw=zoom?1000:g.width,vh=zoom?Math.min(330,g.height):g.height;
      const vx=zoom?Math.max(0,Math.min(g.width-vw,at.x+at.w/2-vw/2)):0;
      const vy=zoom?Math.max(0,Math.min(g.height-vh,at.y-118)):0;
      const picture=svg("svg",{viewBox:[vx,vy,vw,vh].join(" "),width:vw,height:vh,
        role:"img","aria-label":w.tree+": "+tree.nodes.map(nodeText).join("; ")});
      picture.append(svg("title",{},w.tree));
      const defs=svg("defs"),marker=svg("marker",{id,markerWidth:7,markerHeight:7,refX:6,refY:3,orient:"auto",markerUnits:"strokeWidth"});
      marker.append(svg("path",{d:"M0,0 L6,3 L0,6 Z",fill:"#607b8d"}));defs.append(marker);picture.append(defs);
      for(const node of tree.nodes){
        const p=g.positions.get(node.id);
        for(const child of node.children||[]){
          const q=g.positions.get(child);
          picture.append(svg("line",{x1:p.x+p.w/2,y1:p.y+p.h,x2:q.x+q.w/2,y2:q.y,stroke:"#607b8d","stroke-width":2,"marker-end":"url(#"+id+")"}));
        }
        if(node.kind==="leaf"&&node.next!==null){
          const q=g.positions.get(node.next);
          picture.append(svg("line",{x1:p.x+p.w,y1:p.y+46,x2:q.x-2,y2:q.y+46,stroke:"#22816d","stroke-dasharray":"4 3","stroke-width":2,"marker-end":"url(#"+id+")"}));
        }
      }
      for(const node of tree.nodes){
        const p=g.positions.get(node.id),active=highlight.includes(node.id),waiting=node.id===pending;
        const group=svg("g",{"data-page":node.id});
        group.append(svg("rect",{x:p.x,y:p.y,width:p.w,height:p.h,rx:8,fill:waiting?"#fff1c9":active?"#d7ebfa":"#f8fbfd",
          stroke:waiting?"#b26900":active?"#155a88":"#7490a4","stroke-width":active||waiting?3:1.5}));
        group.append(svg("text",{x:p.x+10,y:p.y+23,"font-size":15,"font-family":"system-ui","font-weight":"650",fill:"#18344a"},
          "P"+node.id+" · "+(node.kind==="leaf"?w.leaf:w.internal)));
        group.append(svg("text",{x:p.x+10,y:p.y+49,"font-size":17,"font-family":"system-ui",fill:"#18344a"},
          node.keys.join(" | ")||"∅"));
        if(interactive){group.style.cursor="pointer";group.addEventListener("click",()=>focus(node.id),{signal});}
        picture.append(group);
      }
      frame.replaceChildren(picture);
      if(zoom){
        const pointers=focusNode.kind==="internal"?w.children+": "+focusNode.children.map(id=>"P"+id).join(", "):
          w.nextLeaf+": "+(focusNode.next===null?w.none:"P"+focusNode.next);
        frame.append(el("p",w.pageZoom,{class:"bp-note"}),el("strong",nodeText(focusNode)),el("p",pointers));
      }
    }
  };
}
