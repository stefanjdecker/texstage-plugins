// SPDX-License-Identifier: Apache-2.0
import {canonical} from "./identity.mjs";
import {answerFor} from "./validation.mjs";
import {analyzeSteps, Budget} from "./operations.mjs";
export const copy = value => structuredClone(value);
export const key = value => canonical(value ?? null);
export const isRead = seed => ["lookup","range"].includes(seed.task.kind);
export function blank(seed) {
  if (isRead(seed)) return {path:[seed.tree.root], keys:"", ...(seed.task.kind==="range"?{leaves:[]}: {})};
  return {path:[seed.tree.root], repairs:[],
    separators:seed.tree.nodes.filter(n=>n.kind==="internal").map(n=>({node:String(n.id),keys:""})), height:""};
}
export function fromAnswer(seed, answer) {
  if (!answer) return blank(seed);
  const draft={path:[...answer.path]};
  if (isRead(seed)) return {...draft,keys:answer.keys.join(", "),...(answer.leaves?{leaves:[...answer.leaves]}:{})};
  return {...draft,repairs:answer.repairs.map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,k==="op"?v:String(v)]))),
    separators:answer.separators.map(r=>({node:String(r.node),keys:r.keys.join(", ")})),height:String(answer.height)};
}
export function integer(text,low,high) {
  if (typeof text!=="string" || !/^-?\d+$/.test(text.trim())) throw Error("integer");
  const value=Number(text);
  if(!Number.isSafeInteger(value)||value<low||value>high)throw Error("integer");
  return value;
}
export function numbers(text,limit) {
  if(!text.trim())return [];
  const parts=text.split(",");if(parts.length>limit)throw Error("integer");
  return parts.map(s=>integer(s,-9999,9999));
}
export function toAnswer(seed,draft) {
  const base={format:1,path:[...draft.path]};
  const answer=isRead(seed)?{...base,keys:numbers(draft.keys,seed.task.kind==="lookup"?1:40),
    ...(seed.task.kind==="range"?{leaves:[...draft.leaves]}:{})}:{...base,
    repairs:draft.repairs.map(r=>r.op==="split"?{op:r.op,node:integer(r.node,0,63),
      left_count:integer(r.left_count,1,6),separator:integer(r.separator,-9999,9999)}:
      {op:r.op,node:integer(r.node,0,63),sibling:integer(r.sibling,0,63)}),
    separators:draft.separators.map(r=>({node:integer(r.node,0,63),keys:numbers(r.keys,5)})),
    height:integer(draft.height,0,3)};
  return answerFor(seed,answer);
}
export function steps(answer) {
  return [{kind:"start"},...answer.path.map((_,index)=>({kind:"path",index})),
    ...(answer.leaves||[]).map((_,index)=>({kind:"scan",index})),
    ...(answer.repairs||[]).map((_,index)=>({kind:"repair",index})),{kind:"prediction"}];
}
export function focusIds(answer,focus) {
  if(!focus)return [];
  if(focus.kind==="path")return answer.path.slice(0,focus.index+1);
  if(focus.kind==="scan")return [...answer.path,...answer.leaves.slice(0,focus.index+1)];
  if(focus.kind==="repair")return [answer.repairs[focus.index]?.node,answer.repairs[focus.index]?.sibling].filter(Number.isInteger);
  return [];
}
export async function preview(seed,answer,{signal,valid=()=>true}={}) {
  const generator=analyzeSteps(seed,answer,new Budget(),true),frames=[];
  let maximumChunkMs=0;
  try {
    while(true) {
      await new Promise(resolve=>setTimeout(resolve,0));
      if(signal?.aborted||!valid())return null;
      const start=performance.now(),next=generator.next();
      maximumChunkMs=Math.max(maximumChunkMs,performance.now()-start);
      if(next.done)return {facts:next.value,frames,maximumChunkMs};
      if(next.value)frames.push(next.value);
    }
  } finally {generator.return();}
}
export function frameAt(seed,analysis,focus) {
  if(!analysis||!focus||["start","path","scan"].includes(focus.kind))return {tree:seed.tree,pending:null};
  const frames=analysis.frames.filter(frame=>frame.kind!=="repair"||focus.kind==="prediction"||frame.index<=focus.index);
  return frames.at(-1)||{tree:seed.tree,pending:null};
}
