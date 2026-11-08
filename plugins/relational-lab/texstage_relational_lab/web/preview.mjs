// SPDX-License-Identifier: Apache-2.0
// Cooperative, cancellable public-data calculation. It never submits or grades.
import {Budget, evaluateTreeSteps} from './algebra.mjs';
import {treeFor} from './editor-model.mjs';
const nextTurn=()=>new Promise(resolve=>setTimeout(resolve,0));
const check=signal=>{if(signal?.aborted)throw new DOMException('Preview cancelled','AbortError');};
export async function preview(item,answer,{signal,yieldTurn=nextTurn,now=()=>performance.now(),onChunk=()=>{}}={}) {
  check(signal);
  const tree=treeFor(item,answer),nodes=[];
  const work=evaluateTreeSteps(item,tree,item.instance,new Budget());
  let result,finished=false,chunk=now(),count=0;
  try{
    while(!finished){
      check(signal);result=work.next();finished=result.done;
      if(!finished&&result.value)nodes[result.value.index]=result.value.relation;
      if(!finished&&(now()-chunk>=4||++count>=32)){
        onChunk(now()-chunk);await yieldTurn();check(signal);chunk=now();count=0;
      }
    }
    check(signal);onChunk(now()-chunk);
    return {tree,nodes,...result.value};
  }finally{work.return();}
}
