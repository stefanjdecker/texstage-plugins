// SPDX-License-Identifier: Apache-2.0
// Pure per-plan model. No optimizer search, browser globals, I/O or row iteration.
import {canonical,sha256} from "./identity.mjs";
import {sourceFor,answerFor,DomainError,budget,requireInput} from "./validation.mjs";

export function analyze(source, submission) {
  const exercise = sourceFor(source), answer = answerFor(submission);
  const base = {format:"query-plan-analysis-v1",model:"teaching-cost-v1",
    exercise:sha256(canonical(["query-plan-exercise-v1",exercise])),
    answer:sha256(canonical(["query-plan-answer-v1",answer]))};
  const check = (ok,reason,node=-1) => { if (!ok) throw new DomainError(reason,node); };
  try {
    const nodes = answer.nodes, parents = nodes.map(() => 0);
    nodes.forEach((n,i) => {
      if (n.op === "join") for (const child of [n.left,n.right]) {
        check(child < i,"invalid-tree",i); parents[child]++;
      }
    });
    check(parents.at(-1) === 0 && parents.slice(0,-1).every(n => n === 1),"invalid-tree");
    const order = [];
    const visit = i => {
      if (nodes[i].op === "join") { visit(nodes[i].left); visit(nodes[i].right); }
      order.push(i);
    };
    visit(nodes.length-1);
    check(order.every((v,i) => v === i) && order.length === nodes.length,"invalid-tree");
    const relations = new Map(exercise.query.relations.map(r => [r.id,r]));
    const bits = new Map([...relations.keys()].map((n,i) => [n,1<<i]));
    const stats = new Map(exercise.statistics.base.map(b => [b.relation,b]));
    const cards = new Map(exercise.statistics.cardinalities.map(c => [
      c.relations.reduce((m,n) => m|bits.get(n),0),c.rows]));
    const seen = new Set(), facts = [];
    for (const [i,n] of nodes.entries()) {
      let mask,rows,width,local,total,memory=0;
      if (n.op === "scan") {
        check(relations.has(n.relation),"unknown-relation",i);
        check(!seen.has(n.relation),"duplicate-relation",i); seen.add(n.relation);
        const b = stats.get(n.relation), r = relations.get(n.relation);
        mask = bits.get(n.relation); rows = cards.get(mask); width = b.row_bytes;
        if (n.method === "seq") local = 100*b.pages + b.rows;
        else {
          check(Object.hasOwn(r,"index"),"unavailable-index",i);
          local = 400*(r.index.height + rows) + rows;
        }
        total = local;
      } else {
        const a = facts[n.left], b = facts[n.right];
        check(!(a.subset & b.subset),"duplicate-relation",i);
        mask = a.subset | b.subset;
        check(cards.has(mask),"disconnected-join",i);
        rows = cards.get(mask); width = a.row_bytes + b.row_bytes;
        if (n.method === "nested") local = a.rows*b.rows + rows;
        else {
          const [build,probe] = n.method === "hash-left" ? [a,b] : [b,a];
          memory = build.rows*(build.row_bytes+16);
          check(memory <= exercise.limits.hash_bytes,"hash-memory",i);
          local = 2*build.rows + probe.rows + rows;
        }
        total = local + a.total_cost + b.total_cost;
      }
      requireInput(Number.isSafeInteger(total) && total >= 0 && total <= 3000000000000);
      facts.push({node:i,subset:mask,rows,row_bytes:width,local_cost:local,total_cost:total,hash_bytes:memory});
    }
    check(seen.size === relations.size,"missing-relation");
    const result = {...base,valid:true,cost:facts.at(-1).total_cost,nodes:facts};
    budget(result,8192); return result;
  } catch (error) {
    if (!(error instanceof DomainError)) throw error;
    return {...base,valid:false,reason:error.reason,node:error.node};
  }
}
