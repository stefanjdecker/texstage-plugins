// SPDX-License-Identifier: Apache-2.0
// Pure bounded selector model. It enumerates tree shapes, never costs or optima.
export const copy = value => JSON.parse(JSON.stringify(value));
export {canonical as key} from "./identity.mjs";
import {canonical as key} from "./identity.mjs";
const leaves = tree => typeof tree === "string" ? [tree] : tree.flatMap(leaves);
const subset = tree => leaves(tree).sort().join("\u0000");
export function topology(answer) {
  const visit = i => { const n=answer.nodes[i]; return n.op==="scan" ? n.relation : [visit(n.left),visit(n.right)]; };
  return visit(answer.nodes.length-1);
}
export function label(tree) { return typeof tree==="string" ? tree : "(" + tree.map(label).join(" ⋈ ") + ")"; }
export function topologies(exercise) {
  const ids=exercise.query.relations.map(r=>r.id);
  const connected=new Set(exercise.statistics.cardinalities.map(c=>[...c.relations].sort().join("\u0000")));
  function trees(xs) {
    if(xs.length===1) return [xs[0]];
    const result=[];
    for(let mask=1;mask<(1<<xs.length)-1;mask++) {
      const left=xs.filter((_,i)=>mask&(1<<i)),right=xs.filter((_,i)=>!(mask&(1<<i)));
      if(!connected.has([...left].sort().join("\u0000"))||!connected.has([...right].sort().join("\u0000"))) continue;
      for(const a of trees(left)) for(const b of trees(right)) result.push([a,b]);
    }
    return result;
  }
  return trees(ids);
}
export function retopologize(answer, tree) {
  const scans=new Map(answer.nodes.filter(n=>n.op==="scan").map(n=>[n.relation,n.method]));
  const joins=new Map();
  function remember(i) {
    const n=answer.nodes[i]; if(n.op==="scan") return n.relation;
    const t=[remember(n.left),remember(n.right)]; joins.set(subset(t),n.method); return t;
  }
  remember(answer.nodes.length-1);
  const nodes=[];
  function build(t) {
    if(typeof t==="string") nodes.push({op:"scan",relation:t,method:scans.get(t)||"seq"});
    else {const left=build(t[0]),right=build(t[1]);nodes.push({op:"join",left,right,method:joins.get(subset(t))||"nested"});}
    return nodes.length-1;
  }
  build(tree); return {format:1,nodes};
}
export function supported(exercise, answer) {
  try {
    // Constrain recursion first, including duplicate/unreachable children.
    const seen=new Set();
    function visit(i) {
      if(!Number.isInteger(i)||i<0||i>=answer.nodes.length||seen.has(i)) throw Error();
      seen.add(i); const n=answer.nodes[i];
      if(n.op==="scan") return n.relation;
      if(n.op!=="join"||n.left>=i||n.right>=i) throw Error();
      return [visit(n.left),visit(n.right)];
    }
    const t=visit(answer.nodes.length-1);
    return seen.size===answer.nodes.length && topologies(exercise).some(x=>key(x)===key(t)) &&
      key(retopologize(answer,t))===key(answer);
  } catch {return false;}
}
// Cardinalities/widths are independent of the chosen physical methods. These
// facts explain unavailable choices even when the current plan is infeasible.
export function geometry(exercise, answer) {
  const cards=new Map(exercise.statistics.cardinalities.map(c=>[[...c.relations].sort().join("\u0000"),c.rows]));
  const base=new Map(exercise.statistics.base.map(b=>[b.relation,b]));
  const facts=[];
  for(const n of answer.nodes) {
    if(n.op==="scan") facts.push({relations:[n.relation],rows:cards.get(n.relation),width:base.get(n.relation)?.row_bytes});
    else {
      const a=facts[n.left],b=facts[n.right],relations=[...a.relations,...b.relations].sort();
      facts.push({relations,rows:cards.get(relations.join("\u0000")),width:a.width+b.width,
        leftBytes:a.rows*(a.width+16),rightBytes:b.rows*(b.width+16)});
    }
  }
  return facts;
}
