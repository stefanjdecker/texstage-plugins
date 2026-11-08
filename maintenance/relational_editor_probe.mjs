// SPDX-License-Identifier: Apache-2.0
// Independent Python expectations arrive over stdin; modules come from the wheel.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const config=JSON.parse(fs.readFileSync(0,'utf8'));
const module=name=>import(pathToFileURL(path.join(config.root,'web',name)));
const {preview}=await module('preview.mjs'),model=await module('editor-model.mjs');
const timings=[];
for(const row of config.cases){
  assert(!row.item.reference_tree&&!row.item.instances&&!row.item.worked);
  const chunks=[],start=performance.now();
  const result=await preview(row.item,row.answer,{onChunk:ms=>chunks.push(ms)});
  assert.deepEqual(result.relation,row.expected.relation,row.name);
  assert.deepEqual(result.stats,row.expected.stats,row.name);
  assert.equal(result.nodes.length,result.tree.length);
  for(const [i,relation] of result.nodes.entries())assert.deepEqual([i,relation.rows.length,relation.header.length],result.stats.trace[i]);
  assert.deepEqual(model.pack(model.unpack(result.tree)),result.tree);
  assert.deepEqual(model.replace(result.tree,[],model.unpack(result.tree)),result.tree);
  const history=new model.History(row.answer),different={mode:'construct',tree:[['rel',Object.keys(row.item.relations)[0]]]};history.push(different);assert.deepEqual(history.undo(),row.answer);assert.deepEqual(history.redo(),different);
  timings.push({name:row.name,milliseconds:performance.now()-start,maxChunkMs:Math.max(...chunks)});
}
const row=config.cases[0],cancelled=new AbortController();cancelled.abort();
await assert.rejects(preview(row.item,row.answer,{signal:cancelled.signal}),{name:'AbortError'});
const mid=new AbortController();let ticks=0,yields=0;
await assert.rejects(preview(row.item,row.answer,{signal:mid.signal,now:()=>ticks+=5,yieldTurn:async()=>{yields++;mid.abort();}}),{name:'AbortError'});assert(yields>0);
const tautology=[['eq',['v',1],['v',1]]];
assert.throws(()=>model.nodesOf([['select',0,tautology]]));
assert.throws(()=>model.nodesOf([['rel','r'],['rel','s']]));
assert.throws(()=>model.nodesOf([['rel','r'],['product',0,0]]));
assert.throws(()=>model.pack({row:['select',0,[['eq',['v',1],['v',1]]]],children:[]}));
const history=new model.History(row.answer);for(let i=0;i<50;i++)history.push(row.answer);assert(history.values.length<=40);
console.log(JSON.stringify({cases:config.cases.length,cancellation:true,history:true,bounds:true,timings}));
