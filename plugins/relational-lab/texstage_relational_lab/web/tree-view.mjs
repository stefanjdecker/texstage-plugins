// SPDX-License-Identifier: Apache-2.0
import {canonical} from './identity.mjs';
import {nodesOf,treeFor} from './editor-model.mjs';
import {rewriteTree} from './rewrites.mjs';
import {preview} from './preview.mjs';
import {editorWords,nodeText,errorMessage} from './editor-text.mjs';
import {el,button} from './lesson-ui.mjs';
export function scope(parent){const controller=new AbortController();if(parent?.aborted)controller.abort();else parent?.addEventListener('abort',()=>controller.abort(),{once:true,signal:controller.signal});return controller;}
const outlines=new WeakMap(),tables=new WeakMap();

export function treeOutline(container,tree,w,{selected=[],onSelect,signal}={}) {
  const focused=container.contains(document.activeElement)?document.activeElement.dataset.path:null;
  outlines.get(container)?.abort();const controller=scope(signal);outlines.set(container,controller);
  container.replaceChildren();
  const list=el('ol',undefined,{class:'rl-tree-list','aria-label':w.tree});
  for(const node of nodesOf(tree)){
    const row=el('li',undefined,{class:'rl-tree-row'});
    row.style.setProperty('--depth',String(node.path.length));
    const text=nodeText(node.row,w);
    const control=onSelect?button(text,()=>onSelect(node.path,node.index),controller.signal):el('span',text,{class:'rl-node-label'});
    control.setAttribute('data-path',node.path.join('.'));control.setAttribute('data-node',String(node.index));
    if(onSelect)control.setAttribute('aria-pressed',String(canonical(node.path)===canonical(selected)));
    row.append(control);list.append(row);
  }
  container.append(list);
  if(focused!==null)container.querySelector(`[data-path="${selected.join('.')}"]`)?.focus({preventScroll:true});
}
export function relationTable(container,result,w,signal) {
  tables.get(container)?.abort();const controller=scope(signal);tables.set(container,controller);signal=controller.signal;
  container.replaceChildren();if(!result)return;
  let page=0;const size=12;
  const count=el('p',`${result.rows.length} ${w.rows} · ${result.header.length} ${w.columns}`);
  const wrap=el('div',undefined,{class:'rl-table',tabindex:'0','aria-label':w.result});
  const table=el('table'),caption=el('caption',w.result),head=el('thead'),headrow=el('tr'),body=el('tbody');
  for(const [name,type] of result.header)headrow.append(el('th',`${name} (${type})`,{scope:'col'}));
  head.append(headrow);table.append(caption,head,body);wrap.append(table);
  const previous=button('←',()=>{page--;draw();},signal),next=button('→',()=>{page++;draw();},signal);
  previous.setAttribute('aria-label',w.previousRows);next.setAttribute('aria-label',w.nextRows);
  const position=el('span',undefined,{'aria-live':'polite'}),controls=el('div',undefined,{class:'rl-actions'});
  controls.append(previous,position,next);container.append(count,wrap,controls);
  function draw(){body.replaceChildren();for(const row of result.rows.slice(page*size,(page+1)*size)){const tr=el('tr');for(const value of row)tr.append(el('td',typeof value==='boolean'?w[String(value)]:String(value)));body.append(tr);}previous.disabled=page===0;next.disabled=(page+1)*size>=result.rows.length;controls.hidden=result.rows.length<=size;position.textContent=`${page*size+1}–${Math.min((page+1)*size,result.rows.length)} / ${result.rows.length}`;}
  draw();if(!result.rows.length)container.append(el('p',w.emptyRows));
}
export function stepList(container,item,steps,w) {
  container.replaceChildren(el('h3',w.steps));
  if(!steps.length){container.append(el('p',w.noSteps));return;}
  let tree=item.baseline_tree;const list=el('ol');
  for(const step of steps){const node=nodesOf(tree).find(n=>canonical(n.path)===canonical(step.path));list.append(el('li',`${w.rules[step.rule]} ${w.at} ${node?nodeText(node.row,w):w.selected}`));tree=rewriteTree(item,tree,step);}
  container.append(list);
}
export function previewPanel(ctx,container) {
  const w=editorWords(ctx.language),root=el('section',undefined,{class:'rl-preview','aria-label':w.preview});
  const heading=el('h3',w.preview),note=el('p',w.previewNote,{class:'rl-note'}),status=el('p','',{role:'status','aria-live':'polite'}),selected=el('p'),table=el('div'),metric=el('p');
  root.append(heading,note,status,selected,table,metric);container.append(root);
  let request=null,generation=0,current=null,path=[],answer=null,baseline=null,dead=false;
  const stop=()=>{dead=true;generation++;request?.abort();};ctx.signal.addEventListener('abort',stop,{once:true});
  async function update(next,selection=[]){
    const token=++generation;request?.abort();request=new AbortController();answer=next;path=selection;current=null;table.replaceChildren();metric.textContent='';selected.textContent='';
    if(next.mode==='construct'&&!next.tree.length){status.textContent=w.previewEmpty;return;}
    status.textContent=w.previewBusy;
    try{
      const value=await preview(ctx.item,next,{signal:request.signal});
      if(next.mode==='rewrite'&&!baseline)baseline=await preview(ctx.item,{mode:'rewrite',steps:[]},{signal:request.signal});
      if(dead||token!==generation||ctx.signal.aborted)return;
      current=value;status.textContent='';draw();
    }catch(error){if(dead||token!==generation||error.name==='AbortError')return;status.textContent=error.message?.includes('limit')?w.previewLimit:errorMessage(error,w);}
  }
  function draw(){
    if(!current)return;
    const node=nodesOf(current.tree).find(n=>canonical(n.path)===canonical(path))||nodesOf(current.tree)[0];
    selected.textContent=nodeText(node.row,w);relationTable(table,current.nodes[node.index],w,ctx.signal);
    metric.textContent=answer.mode==='rewrite'?`${w.baselineCells}: ${baseline.stats.cells}. ${w.currentCells}: ${current.stats.cells}. ${w.metricNote}`:`${w.currentCells}: ${current.stats.cells}. ${w.metricNote}`;
  }
  return {update,select(next){path=next;draw();},clear(){generation++;request?.abort();current=null;table.replaceChildren();status.textContent=w.unapplied;},destroy(){stop();root.remove();}};
}
export function answerPanel(ctx,container) {
  const w=editorWords(ctx.language),root=el('section',undefined,{class:'rl-answer-panel'});container.append(root);
  let identity=null,dispose=()=>{};
  return {update(answer){
    const key=canonical(answer||null);if(key===identity)return;identity=key;dispose();root.replaceChildren();root.hidden=!answer;if(!answer)return;
    const controller=new AbortController();ctx.signal.addEventListener('abort',()=>controller.abort(),{once:true,signal:controller.signal});
    const child={...ctx,signal:controller.signal};dispose=()=>controller.abort();
    try{
      const tree=treeFor(ctx.item,answer),body=el('div',undefined,{class:'rl-answer-body'}),grid=el('div',undefined,{class:'rl-comparison'}),pane=el('div'),outline=el('div');pane.append(el('h3',w.after),outline);
      if(answer.mode==='rewrite'){const before=el('div'),original=el('div');before.append(el('h3',w.before),original);treeOutline(original,ctx.item.baseline_tree,w,{signal:controller.signal});grid.append(before);}
      grid.append(pane);body.append(grid);root.append(body);const panel=previewPanel(child,body);let selected=[];
      const select=path=>{selected=path;render();panel.select(path);};
      const render=()=>treeOutline(outline,tree,w,{selected,onSelect:select,signal:controller.signal});
      render();panel.update(answer);
      if(answer.mode==='rewrite'){const details=el('details');details.append(el('summary',w.steps));const steps=el('div');stepList(steps,ctx.item,answer.steps,w);details.append(steps);root.append(details);}
    }catch(error){root.append(el('p',errorMessage(error,w),{role:'status'}));}
  },destroy(){dispose();root.remove();}};
}
