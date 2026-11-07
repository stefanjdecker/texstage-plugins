// SPDX-License-Identifier: Apache-2.0
const test=require("node:test"),assert=require("node:assert/strict");
const {verifyWorkload}=require("./normalization_load_checks.cjs");
function complete(){
 const submissions=[],events=[];
 for(const phase of ["initial","replacement-old","replacement-latest","multi-registration","multi-classify","reconnect"])
  for(let actor=0;actor<2;actor++){
   const id=phase+"-"+actor,generation=phase==="reconnect"?2:1;
   const row={phase,actor,accepted:true,jobs:[id]};
   if(phase!=="replacement-old"){
    row.checked_ms=50;
    events.push({event:"finish",id,generation,accepted:true,outcome:"ok"});
   }
   submissions.push(row);
   events.push({event:"lease",jobs:[{id,generation}]});
  }
 return {actors:2,submissions,events,reconnect:true};
}
test("completed latest answers and two genuinely retried leases pass",()=>{
 assert.deepEqual(verifyWorkload(complete()),{failures:[],reconnect_abandoned_jobs_recovered:2});
});
const changes={
 "missing whole phase":x=>x.submissions=x.submissions.filter(r=>r.phase!=="multi-classify"),
 "duplicate actor":x=>x.submissions[1].actor=0,
 "refused submission":x=>x.submissions[0].accepted=false,
 "missing durable job":x=>x.submissions[0].jobs=[],
 "unchecked latest answer":x=>delete x.submissions[0].checked_ms,
 "missing accepted result":x=>x.events=x.events.filter(e=>e.id!=="initial-0"),
 "rejected result":x=>x.events.find(e=>e.id==="initial-0").accepted=false,
 "failed result":x=>x.events.find(e=>e.id==="initial-0").outcome="timeout",
 "retry did not happen":x=>x.events.filter(e=>e.event==="lease").forEach(e=>e.jobs[0].generation=1),
 "old generation only":x=>x.events.find(e=>e.id==="reconnect-0").generation=1,
 "unrelated retry":x=>x.events.filter(e=>e.event==="lease"&&e.jobs[0].generation===2).forEach(e=>e.jobs[0].id="another-item"),
};
for(const [name,change] of Object.entries(changes))test(name+" cannot pass",()=>{
 const value=complete();change(value);assert(verifyWorkload(value).failures.length>0);
});
test("an explicitly requested smoke run does not claim abandoned-job coverage",()=>{
 const value=complete();value.reconnect=false;
 value.submissions=value.submissions.filter(r=>r.phase!=="reconnect");
 value.events=value.events.filter(e=>e.event==="finish"?!e.id.startsWith("reconnect"):!e.jobs[0].id.startsWith("reconnect"));
 assert.deepEqual(verifyWorkload(value),{failures:[],reconnect_abandoned_jobs_recovered:0});
});


test("guarded cached deliveries count, incomplete or failed deliveries do not",()=>{
 const value=complete(),event=value.events.find(e=>e.id==="initial-0");
 Object.assign(event,{event:"delivery",delivered:true,status:"succeeded"});
 assert.deepEqual(verifyWorkload(value).failures,[]);
 event.delivered=false;assert(verifyWorkload(value).failures.length);
 event.delivered=true;event.status="failed";assert(verifyWorkload(value).failures.length);
 event.status="succeeded";event.outcome="timeout";assert(verifyWorkload(value).failures.length);
});
