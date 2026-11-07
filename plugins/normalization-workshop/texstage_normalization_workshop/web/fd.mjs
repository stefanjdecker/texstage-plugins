// SPDX-License-Identifier: Apache-2.0
import {ResourceLimit} from "./validation.mjs";
export const subset=(a,b)=>(a & b) === a;
export const popcount=n=>{ let k=0; for (;n;n&=n-1) k++; return k; };
export class Budget {
  constructor(limit=1000000) { this.remaining=limit; this.used=0; }
  tick(count=1) { this.remaining-=count; this.used+=count; if(this.remaining<0) throw new ResourceLimit("work"); }
}
export class Theory {
  constructor(exercise,budget=new Budget()) {
    this.n=exercise.attributes.length; this.universe=(1<<this.n)-1;
    this.fds=exercise.fds; this.budget=budget; this.closures=[]; this.forms=new Map();
    for(let mask=0;mask<=this.universe;mask++) {
      let found=mask, previous;
      do {
        previous=found;
        for(const [left,right] of this.fds) { budget.tick(); if(subset(left,found)) found|=right; }
      } while(found!==previous);
      this.closures.push(found);
    }
  }
  describe(relation) {
    if(this.forms.has(relation)) return this.forms.get(relation);
    const masks=Array.from({length:this.universe+1},(_,i)=>i).filter(x=>subset(x,relation))
      .sort((a,b)=>popcount(a)-popcount(b)||a-b);
    const keys=[];
    for(const mask of masks) {
      this.budget.tick();
      if((this.closures[mask] & relation)!==relation) continue;
      let minimal=true;
      for(const k of keys) { this.budget.tick(); if(subset(k,mask)) { minimal=false; break; } }
      if(minimal) keys.push(mask);
    }
    const prime=keys.reduce((a,b)=>a|b,0);
    const witnesses={"2nf":null,"3nf":null,bcnf:null};
    for(const left of masks) {
      const reached=this.closures[left] & relation;
      for(let j=0;j<this.n;j++) {
        this.budget.tick(); const right=1<<j;
        if(!(right & reached) || (right & left)) continue;
        if(reached!==relation) {
          witnesses.bcnf ??= [left,right];
          if(!(right & prime)) witnesses["3nf"] ??= [left,right];
        }
        if(!(right & prime)) for(const key of keys) {
          this.budget.tick();
          if(left!==key && subset(left,key)) { witnesses["2nf"] ??= [left,right]; break; }
        }
      }
    }
    const normal_form=!witnesses.bcnf?"bcnf":!witnesses["3nf"]?"3nf":!witnesses["2nf"]?"2nf":"1nf";
    const value={description:{relation,normal_form,prime,witnesses},keys:keys.sort((a,b)=>a-b)};
    this.forms.set(relation,value); return value;
  }
  witnessValid(claim,witness) {
    if(claim==="bcnf") return witness===null;
    if(witness===null) return false;
    const [left,right]=witness, {description,keys}=this.describe(this.universe);
    if((left & right) || !(this.closures[left] & right)) return false;
    if(claim==="1nf") return !(right & description.prime) && keys.some(k=>left!==k && subset(left,k));
    return this.closures[left]!==this.universe && (claim==="3nf" || !(right & description.prime));
  }
  preservation(parts) {
    for(const [index,[left,right]] of this.fds.entries()) {
      let reached=left, previous;
      do {
        previous=reached;
        for(const part of parts) {
          this.budget.tick();
          reached |= this.closures[reached & part] & part;
        }
      } while(reached!==previous);
      if(!(reached & right)) return {preserved:false,fd:index,closure:reached};
    }
    return {preserved:true,fd:-1,closure:0};
  }
}
