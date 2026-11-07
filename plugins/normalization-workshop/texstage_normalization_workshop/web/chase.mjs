// SPDX-License-Identifier: Apache-2.0
export function chase(theory,parts) {
  const n=theory.n,m=parts.length;
  const table=parts.map((part,i)=>Array.from({length:n},(_,j)=>part & (1<<j)?j:n+i*n+j));
  const merges=[];
  let before;
  do {
    before=merges.length;
    for(const [f,[left,right]] of theory.fds.entries()) {
      const col=Math.log2(right), determinant=Array.from({length:n},(_,j)=>j).filter(j=>left & (1<<j));
      for(let i=0;i<m;i++) for(let k=i+1;k<m;k++) {
        theory.budget.tick();
        if(!determinant.every(j=>table[i][j]===table[k][j])) continue;
        const a=table[i][col], b=table[k][col];
        if(a===b) continue;
        const keep=Math.min(a,b),remove=Math.max(a,b);
        for(const row of table) { theory.budget.tick(); if(row[col]===remove) row[col]=keep; }
        merges.push([f,i,k]);
      }
    }
  } while(merges.length!==before);
  if(merges.length>n*(m-1)) throw new Error("chase-bound");
  return {lossless:table.some(row=>row.every((x,j)=>x===j)),rows:m,columns:n,merges,tableau:table};
}
