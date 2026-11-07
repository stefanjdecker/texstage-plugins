// SPDX-License-Identifier: Apache-2.0
// Presentation of verified facts, not a second grading engine.
export const columns = (mask, n) => Array.from({length:n},(_,i)=>i).filter(i=>mask & (1<<i));
export function chaseFrames(item, answer, data) {
  const join=data.facts.join;
  if(!join || answer.mode!=="decompose")return [];
  const n=item.attributes.length;
  let table=answer.relations.map((mask,i)=>Array.from({length:n},(_,j)=>mask&(1<<j)?j:n+i*n+j));
  const frames=[{table:structuredClone(table),merge:null}];
  for(const [f,i,k] of join.merges){
    const [left,right]=item.fds[f],col=Math.log2(right),x=table[i][col],y=table[k][col];
    if(!Number.isInteger(col)||x===y||!columns(left,n).every(j=>table[i][j]===table[k][j]))throw Error("Invalid chase step");
    const representative=Math.min(x,y);
    table=table.map(row=>row.map((value,j)=>j===col&&(value===x||value===y)?representative:value));
    frames.push({table:structuredClone(table),merge:{fd:f,first:i,second:k,column:col}});
  }
  if(JSON.stringify(table)!==JSON.stringify(join.tableau))throw Error("Chase tableau mismatch");
  return frames;
}
export function joinWitness(item, answer, data){
  const join=data.facts.join;
  if(!join)return null;
  const n=item.attributes.length,target=Array.from({length:n},(_,i)=>i),table=join.tableau;
  const row=table.findIndex(r=>r.every((v,j)=>v===target[j]));
  if((row>=0)!==join.lossless)throw Error("Invalid lossless witness");
  const projections=answer.relations.map((mask,i)=>{
    const indices=columns(mask,n);
    if(!indices.every(j=>table[i][j]===target[j]))throw Error("Missing component witness");
    return {relation:mask,row:i,values:indices.map(j=>table[i][j])};
  });
  return {table:structuredClone(table),target,row,projections};
}
export function lostDependency(item, data){
  const proof=data.facts.preservation;
  if(!proof || proof.preserved)return null;
  const n=item.attributes.length,dependency=item.fds[proof.fd],closed=proof.closure;
  if((closed & dependency[0])!==dependency[0] || (closed & dependency[1]))throw Error("Invalid closure witness");
  // These rows deliberately violate the lost original FD. Each component's
  // projection satisfies its own projected FDs because the equal columns form
  // a closed set for their union. This is NOT a legal original-FD relation.
  return {dependency:[...dependency],closure:closed,
    rows:[Array.from({length:n},(_,j)=>j),Array.from({length:n},(_,j)=>closed&(1<<j)?j:2*n+j)]};
}
export function symbol(value, column, item){
  const n=item.attributes.length,id=item.attributes[column].id;
  return value===column?"a_"+id:"b"+(Math.floor((value-n)/n)+1)+"_"+id;
}
