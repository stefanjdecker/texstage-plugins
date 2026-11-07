// SPDX-License-Identifier: Apache-2.0
// Evidence checks for the synthetic workload; never changes runtime behavior.
const phases=["initial","replacement-old","replacement-latest","multi-registration","multi-classify"];
function verifyWorkload({actors,submissions,events,reconnect}){
 const failures=[],required=[...phases,...(reconnect?["reconnect"]:[])];
 for(const phase of required){
  const rows=submissions.filter(r=>r.phase===phase);
  if(rows.length!==actors||new Set(rows.map(r=>r.actor)).size!==actors)
   failures.push(phase+": missing or duplicate actor");
  for(const row of rows){
   if(!row.accepted||row.jobs?.length!==1)failures.push(phase+": missing accepted job");
   if(phase!=="replacement-old"){
    if(!Number.isFinite(row.checked_ms))failures.push(phase+": latest answer never checked");
    if(!events.some(e=>((e.event==="finish"&&e.accepted)||(e.event==="delivery"&&e.delivered&&e.status==="succeeded"))&&row.jobs?.includes(e.id)&&e.outcome==="ok"))
     failures.push(phase+": missing accepted successful result");
   }
  }
 }
 const retryRows=submissions.filter(r=>r.phase==="reconnect"),retryIds=new Set(retryRows.flatMap(r=>r.jobs||[]));
 const recovered=new Set();
 for(const e of events){
  if(e.event!=="lease")continue;
  for(const j of e.jobs||[]){
   if(j.generation!==2||!retryIds.has(j.id))continue;
   if(events.some(f=>f.event==="finish"&&f.id===j.id&&f.generation===j.generation&&f.accepted&&f.outcome==="ok"))
    recovered.add(j.id);
  }
 }
 if(reconnect&&recovered.size!==2)failures.push("reconnect: both abandoned jobs must complete in generation 2");
 return {failures,reconnect_abandoned_jobs_recovered:recovered.size};
}
module.exports={verifyWorkload};
