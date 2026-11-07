// SPDX-License-Identifier: Apache-2.0
// Pure helpers from the installed wheel, including cancellable shared replay.
import fs from "node:fs";
import assert from "node:assert/strict";
const config=JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
const editor=await import(config.editor),tree=await import(config.tree),locale=await import(config.locale);
const report={roundtrips:0,replays:0,frames:0,maximumChunkMs:0};
for(const row of config.cases){
  const draft=editor.fromAnswer(row.seed,row.answer),answer=editor.toAnswer(row.seed,draft);
  assert.deepEqual(answer,row.answer);report.roundtrips++;
  const unchanged=JSON.stringify([row.seed,row.answer]);
  const result=await editor.preview(row.seed,answer);
  assert.deepEqual(result.facts,row.facts);assert.equal(JSON.stringify([row.seed,row.answer]),unchanged);
  report.replays++;report.frames+=result.frames.length;report.maximumChunkMs=Math.max(report.maximumChunkMs,result.maximumChunkMs);
  assert(result.frames.length<=5);
  const g=tree.geometry(row.seed.tree);
  assert.equal(g.positions.size,row.seed.tree.nodes.length);
  for(const p of g.positions.values()){assert(p.x>=0&&p.y>=0&&p.x+p.w<=g.width&&p.y+p.h<=g.height);}
  const steps=editor.steps(answer);
  for(const focus of steps){assert(editor.focusIds(answer,focus).every(Number.isInteger));assert(editor.frameAt(row.seed,result,focus).tree);}
  result.frames[0].tree.nodes[0].keys.push(12345);
  assert.equal(JSON.stringify([row.seed,row.answer]),unchanged);
}
const first=config.cases[0],abort=new AbortController();abort.abort();
assert.equal(await editor.preview(first.seed,first.answer,{signal:abort.signal}),null);
let ticks=0;
assert.equal(await editor.preview(first.seed,first.answer,{valid:()=>++ticks<2}),null);
assert(ticks>=2);
for(const bad of ["", "NaN","1e2","1.5","10000","--1","+1","1 2","0x10"])
  assert.throws(()=>editor.integer(bad,-9999,9999));
assert.deepEqual(editor.numbers(" -20, 0, 25 ",5),[-20,0,25]);assert.throws(()=>editor.numbers("1,,2",5));
for(const [key,value]of Object.entries(locale.languages.en)){
  assert(key in locale.languages.de,key);
  if(key==="reason")assert.deepEqual(Object.keys(value).sort(),Object.keys(locale.languages.de.reason).sort());
}
assert.equal(locale.local({en:"English"},"de-AT"),"English");
assert.equal(locale.words("de-AT").save,locale.languages.de.save);
assert(!JSON.stringify(config).includes("javascript:"));
console.log(JSON.stringify(report));
