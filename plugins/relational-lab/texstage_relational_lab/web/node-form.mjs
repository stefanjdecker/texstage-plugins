// SPDX-License-Identifier: Apache-2.0
import {id} from './validation.mjs';
import {columnsFor,at,unpack,clone} from './editor-model.mjs';
import {operators} from './editor-text.mjs';
import {el,button} from './lesson-ui.mjs';
import {scope} from './tree-view.mjs';
export const field=(label,input)=>{const wrap=el('label',label);wrap.append(input);if(input.type==='checkbox')wrap.className='rl-check';return wrap;};
export function picker(values,value,label){const input=el('select',undefined,{'aria-label':label});for(const [key,text] of values)input.append(el('option',text,{value:key}));input.value=value;if(input.selectedIndex<0)input.selectedIndex=0;return input;}
const fail=code=>{throw new Error(code);};
export function defaultTerm(columns){const type=columns[0]?.[1]||'bool';return ['v',type==='text'?'':type==='int'?0:true];}
function operand(parent,term,columns,w,label,signal){
  const kinds=[['a',w.attribute],['int',w.int],['text',w.text],['bool',w.bool]];
  const kind=picker(kinds,term[0]==='a'?'a':typeof term[1]==='boolean'?'bool':typeof term[1]==='number'?'int':'text',label+' · '+w.kind);
  const box=el('div',undefined,{class:'rl-operand'}),valueBox=el('div');box.append(field(label+' · '+w.kind,kind),valueBox);parent.append(box);let input;
  function render(initial){valueBox.replaceChildren();
    if(kind.value==='a'){
      const options=columns.map(([n,t])=>[n,n+' ('+t+')']);if(initial?.[0]==='a'&&!options.some(v=>v[0]===initial[1]))options.push([initial[1],initial[1]+' (?)']);
      input=picker(options,initial?.[0]==='a'?initial[1]:options[0]?.[0],label+' · '+w.attribute);
    }else if(kind.value==='bool')input=picker([['true',w.true],['false',w.false]],String(initial?.[0]==='v'?initial[1]:true),label+' · '+w.value);
    else{input=el('input',undefined,{type:'text','aria-label':label+' · '+w.value,...(kind.value==='int'?{inputmode:'numeric'}:{maxlength:'48'})});input.value=initial?.[0]==='v'?String(initial[1]):kind.value==='int'?'0':'';}
    valueBox.append(field(label+(kind.value==='a'?' · '+w.attribute:' · '+w.value),input));
  }
  kind.addEventListener('change',()=>render(),{signal});render(term);
  return ()=>{
    if(kind.value==='a'){if(!id(input.value))fail('unknown-attribute');return ['a',input.value];}
    if(kind.value==='bool')return ['v',input.value==='true'];
    if(kind.value==='int'){if(!/^-?(0|[1-9][0-9]*)$/.test(input.value.trim()))fail('integer');const n=Number(input.value);if(!Number.isSafeInteger(n)||Math.abs(n)>1000000)fail('integer');return ['v',n];}
    const text=input.value.normalize('NFC');if([...text].length>24)fail('text');return ['v',text];
  };
}
function predicates(parent,atoms,columns,w,signal,changed){
  const section=el('fieldset'),legend=el('legend',w.conditions),rows=el('div');section.append(legend,rows);parent.append(section);
  let entries=[];
  function add(atom){
    const controller=scope(signal),row=el('fieldset',undefined,{class:'rl-condition'}),label=el('legend',w.condition+' '+(entries.length+1));row.append(label);
    const left=operand(row,atom[1],columns,w,w.left,controller.signal);
    const comparison=picker(Object.entries(operators),atom[0],w.comparison);row.append(field(w.comparison,comparison));
    const right=operand(row,atom[2],columns,w,w.right,controller.signal);
    const entry={row,controller,read:()=>[comparison.value,left(),right()]};
    const remove=button(w.removeCondition,()=>{controller.abort();row.remove();entries=entries.filter(e=>e!==entry);refresh();changed();},controller.signal);row.append(remove);entry.remove=remove;
    entries.push(entry);rows.append(row);refresh();
  }
  const more=button(w.addCondition,()=>{add(['eq',columns.length?['a',columns[0][0]]:['v',true],defaultTerm(columns)]);changed();},signal);section.append(more);
  function refresh(){more.disabled=entries.length>=3;for(const [i,e] of entries.entries()){e.remove.disabled=entries.length===1;e.row.querySelector('legend').textContent=w.condition+' '+(i+1);}}
  atoms.forEach(add);return ()=>entries.map(e=>e.read());
}
export function nodeForm(parent,item,tree,path,w,signal,changed){
  const row=clone(at(unpack(tree),path).row),op=row[0],wrap=el('div',undefined,{class:'rl-node-form'});parent.append(wrap);
  const columns=op==='join'?[...columnsFor(item,tree,path,0),...columnsFor(item,tree,path,1)]:columnsFor(item,tree,path,0);
  let read;
  if(op==='rel'){const input=picker(Object.keys(item.relations).map(n=>[n,n]),row[1],w.relation);wrap.append(field(w.relation,input));read=()=>[op,input.value];}
  else if(op==='select'||op==='join'){const values=predicates(wrap,row.at(-1),columns,w,signal,changed);read=()=>[...row.slice(0,-1),values()];}
  else if(op==='project'){
    const group=el('fieldset',undefined,{class:'rl-column-checks'});group.append(el('legend',w.project));const names=[...new Set([...columns.map(c=>c[0]),...row[2]])],inputs=[];
    for(const name of names){const input=el('input',undefined,{type:'checkbox',value:name});input.checked=row[2].includes(name);group.append(field(name,input));inputs.push(input);}wrap.append(group);
    read=()=>{const names=inputs.filter(x=>x.checked).map(x=>x.value);if(!names.length)fail('empty-project');return [op,row[1],names];};
  }else if(op==='rename'){
    wrap.append(el('p',w.renameHint));const mapping=new Map(row[2]),names=[...new Set([...columns.map(c=>c[0]),...mapping.keys()])],inputs=[];
    for(const name of names){const input=el('input',undefined,{type:'text','aria-label':name+' →',maxlength:'12',spellcheck:'false'});input.value=mapping.get(name)||name;wrap.append(field(name+' →',input));inputs.push([name,input]);}
    read=()=>{const pairs=inputs.filter(([name,input])=>input.value!==name).map(([name,input])=>[name,input.value]);if(!pairs.length)fail('empty-rename');if(pairs.some(p=>!id(p[1])))fail('name');return [op,row[1],pairs];};
  }else{wrap.append(el('p',w.selectNode));read=()=>row;}
  for(const event of ['input','change'])wrap.addEventListener(event,changed,{signal});
  return {read,editable:['rel','select','join','project','rename'].includes(op)};
}
