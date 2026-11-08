// SPDX-License-Identifier: Apache-2.0
import {canonical} from './identity.mjs';
import {rewriteTree} from './rewrites.mjs';
import {CHILDREN,answerFor} from './validation.mjs';
import {clone,at,unpack,pack,replace,treeFor,columnsFor,starter,structuralError,History} from './editor-model.mjs';
import {editorWords,nodeText,errorMessage} from './editor-text.mjs';
import {treeOutline,previewPanel,stepList,scope} from './tree-view.mjs';
import {nodeForm,picker,field,defaultTerm} from './node-form.mjs';
import {el,button} from './lesson-ui.mjs';

export function createEditor(ctx,container,changed){
  const w=editorWords(ctx.language),root=el('section',undefined,{class:'rl-editor','aria-label':w.title});container.append(root);
  const history=new History(starter(ctx.item)),actions=el('div',undefined,{class:'rl-actions'}),grid=el('div',undefined,{class:'rl-editor-grid'}),treePane=el('div'),outline=el('div'),inspector=el('section',undefined,{class:'rl-inspector'}),details=el('div'),switches=el('div',undefined,{class:'rl-actions'}),previewHost=el('div');
  const message=el('p','',{role:'status','aria-live':'polite'}),error=el('p','',{role:'alert'}),steps=el('div');
  treePane.append(el('h3',w.tree),el('p',w.selectNode),outline);details.append(switches,inspector,previewHost);grid.append(treePane,details);root.append(actions,message,error,grid,steps);
  const result=previewPanel(ctx,previewHost);
  const editTab=button(w.edit,()=>show(false),ctx.signal),resultTab=button(w.result,()=>show(true),ctx.signal);switches.append(editTab,resultTab);
  function show(inspect){inspector.hidden=inspect;previewHost.hidden=!inspect;editTab.setAttribute('aria-pressed',String(!inspect));resultTab.setAttribute('aria-pressed',String(inspect));}show(false);
  let selected=[],formDirty=false,formScope=null,form=null,apply=null,discard=null,dead=false;
  const undo=button(w.undo,()=>guard(()=>{history.undo();render();changed();}),ctx.signal),redo=button(w.redo,()=>guard(()=>{history.redo();render();changed();}),ctx.signal),reset=button(w.startOver,()=>guard(()=>commit(starter(ctx.item))),ctx.signal);
  actions.append(undo,redo,reset);
  function guard(fn){if(formDirty){message.textContent=w.unapplied;return;}try{error.textContent='';fn();}catch(e){error.textContent=errorMessage(e,w);}}
  function commit(answer,path=[]){if(answer.mode!=='construct'||answer.tree.length)answerFor(answer);history.push(answer);selected=path;formDirty=false;render();changed();}
  function mark(){formDirty=true;message.textContent=w.unapplied;error.textContent='';if(apply)apply.disabled=false;if(discard)discard.disabled=false;result.clear();changed();}
  function render(){
    if(dead)return;
    formScope?.abort();formScope=scope(ctx.signal);const signal=formScope.signal;
    inspector.replaceChildren();steps.replaceChildren();formDirty=false;form=null;apply=discard=null;message.textContent='';error.textContent='';
    undo.disabled=history.index===0;redo.disabled=history.index+1===history.values.length;
    const answer=history.value;
    let tree;
    try{tree=answer.mode==='construct'?answer.tree:treeFor(ctx.item,answer);if(tree.length)try{at(unpack(tree),selected);}catch{selected=[];}}
    catch(e){outline.replaceChildren(el('p',errorMessage(e,w)));result.clear();return;}
    if(!tree.length){outline.replaceChildren(el('p',w.empty));const table=picker(Object.keys(ctx.item.relations).map(n=>[n,n]),Object.keys(ctx.item.relations)[0],w.relation);inspector.append(field(w.relation,table),button(w.addTable,()=>guard(()=>commit({mode:'construct',tree:[['rel',table.value]]})),signal));result.update(answer);return;}
    const select=path=>guard(()=>{selected=path;render();});
    try{treeOutline(outline,tree,w,{selected,onSelect:select,signal});}
    catch(e){outline.replaceChildren(el('p',errorMessage(e,w)));error.textContent=errorMessage(e,w);return;}
    const current=at(unpack(tree),selected);inspector.append(el('h3',w.selected),el('p',nodeText(current.row,w),{class:'rl-selected'}));
    if(answer.mode==='rewrite')renderRules(answer,tree,signal);
    else renderConstruct(answer,tree,current,signal);
    const invalid=structuralError(ctx.item,answer);if(invalid)error.textContent=errorMessage(invalid,w);
    result.update(answer,selected);
  }
  function renderRules(answer,tree,signal){
    const rule=picker(ctx.item.task.allowed_rules.map(r=>[r,w.rules[r]]),ctx.item.task.allowed_rules[0],w.rule),reason=el('p'),applyRule=button(w.applyRule,()=>guard(()=>{if(answer.steps.length>=8)throw new Error('steps');rewriteTree(ctx.item,tree,{rule:rule.value,path:selected});commit({mode:'rewrite',steps:[...answer.steps,{rule:rule.value,path:[...selected]}]},selected);}),signal);
    function available(){try{if(answer.steps.length>=8)throw new Error('steps');rewriteTree(ctx.item,tree,{rule:rule.value,path:selected});reason.textContent='';applyRule.disabled=false;}catch(e){reason.textContent=errorMessage(e,w);applyRule.disabled=true;}}
    rule.addEventListener('change',available,{signal});inspector.append(field(w.rule,rule),reason,applyRule);available();stepList(steps,ctx.item,answer.steps,w);
  }
  function renderConstruct(answer,tree,current,signal){
    form=nodeForm(inspector,ctx.item,tree,selected,w,signal,mark);
    if(form.editable){
      apply=button(w.apply,()=>{try{const node=at(unpack(tree),selected);node.row=form.read();const next=replace(tree,selected,node);commit({mode:'construct',tree:next},selected);}catch(e){error.textContent=errorMessage(e,w);}},signal);
      discard=button(w.discard,()=>{formDirty=false;render();changed();},signal);apply.disabled=discard.disabled=true;inspector.append(apply,discard);
    }
    const extra=el('details');extra.open=true;extra.append(el('summary',w.operator));
    const allowed=ctx.item.task.allowed_operators.filter(x=>x!=='rel'),operator=picker(allowed.map(k=>[k,w.labels[k]]),allowed[0],w.operator),tables=Object.keys(ctx.item.relations),other=picker(tables.map(n=>[n,n]),tables.find(n=>n!==current.row[1])||tables[0],w.otherRelation),otherField=field(w.otherRelation,other);
    const refresh=()=>{otherField.hidden=CHILDREN[operator.value]?.length!==2;};operator.addEventListener('change',refresh,{signal});refresh();
    const add=button(w.addOperator,()=>guard(()=>{
      const op=operator.value,left=at(unpack(tree),selected),columns=columnsFor(ctx.item,tree,selected),right={row:['rel',other.value],children:[]};let row;
      if(op==='project'){if(!columns.length)throw new Error('unknown-attribute');row=[op,0,[columns[0][0]]];}
      else if(op==='rename'){if(!columns.length)throw new Error('unknown-attribute');let name=columns[0][0].slice(0,9)+'_2';let suffix=2;while(columns.some(c=>c[0]===name))name=columns[0][0].slice(0,8)+'_'+(++suffix);row=[op,0,[[columns[0][0],name]]];}
      else if(op==='select')row=[op,0,[['eq',columns.length?['a',columns[0][0]]:['v',true],defaultTerm(columns)]]];
      else if(op==='join'){const rightColumns=ctx.item.relations[other.value],pair=columns.flatMap(a=>rightColumns.filter(b=>a[1]===b[1]).map(b=>[a[0],b[0]]))[0];row=[op,0,0,[['eq',pair?['a',pair[0]]:['v',true],pair?['a',pair[1]]:['v',true]]]];}
      else row=[op,0,0];
      const node={row,children:CHILDREN[op].length===1?[left]:[left,right]};commit({mode:'construct',tree:replace(tree,selected,node)},selected);
    }),signal);add.disabled=!allowed.length;extra.append(field(w.operator,operator),otherField,add);
    const replacePanel=el('details');replacePanel.append(el('summary',w.replaceRelation));
    const replacement=picker(tables.map(n=>[n,n]),tables[0],w.replaceRelation);replacePanel.append(field(w.replaceRelation,replacement),button(w.replace,()=>guard(()=>commit({mode:'construct',tree:replace(tree,selected,{row:['rel',replacement.value],children:[]})},selected)),signal));
    if(current.children.length===1)replacePanel.append(button(w.remove,()=>guard(()=>commit({mode:'construct',tree:replace(tree,selected,current.children[0])},selected)),signal));
    if(current.children.length===2){for(const [side,label] of [[0,w.keepLeft],[1,w.keepRight]])replacePanel.append(button(label,()=>guard(()=>commit({mode:'construct',tree:replace(tree,selected,current.children[side])},selected)),signal));replacePanel.append(button(w.swap,()=>guard(()=>commit({mode:'construct',tree:replace(tree,selected,{row:current.row,children:[current.children[1],current.children[0]]})},selected)),signal));}
    extra.append(replacePanel);
    inspector.append(extra);
  }
  render();
  return {
    value:()=>history.value,
    pending:()=>formDirty,
    valid:()=>!formDirty&&(!history.value.tree||history.value.tree.length>0)&&!structuralError(ctx.item,history.value),
    setValue(answer){history.reset(answer);selected=[];formDirty=false;render();},
    destroy(){dead=true;formScope?.abort();result.destroy();root.remove();}
  };
}
