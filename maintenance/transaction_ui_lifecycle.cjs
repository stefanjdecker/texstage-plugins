// SPDX-License-Identifier: Apache-2.0
// Artificial completion order against real installed modules, complementing live UI tests.
module.exports=async function lifecycle(page,urls,exercise){return page.evaluate(async({urls,exercise})=>{
 const module=await import(urls.participant),controlModule=await import(urls.controls);
 const check=(condition,message)=>{if(!condition)throw Error('Transaction lifecycle: '+message);};
 const wait=()=>new Promise(r=>setTimeout(r,25));
 const view=(epoch=1,revision=1,extra={})=>({epoch,revision,data:{format:1,phase:'predict',phase_token:1,active:true,paused:false,cursor:0,prediction_revealed:false,...extra}});
 function make(mod,role='participant'){const container=document.createElement('div'),signal=new AbortController(),requests=[];document.body.append(container);
  const handle=mod.mount({container,item:{format:1,exercise},language:'en',role,signal:signal.signal,dispatch(op,payload){return new Promise((resolve,reject)=>requests.push({op,payload,resolve,reject}));}});
  return{handle,requests,container,get:s=>container.querySelector(s),destroy(){signal.abort();handle.destroy();check(container.childElementCount===0,'disposed root remains');container.remove();}};}
 const p=make(module);p.handle.update(view());const input=p.get('[data-tx-value]'),save=p.get('[data-tx-submit="prediction"]');input.value='110';input.dispatchEvent(new Event('input',{bubbles:true}));save.click();check(p.requests.length===1,'missing save');
 const own={version:1,prediction:{version:1,answer:{values:{x:110}},status:'saved'}};
 p.handle.update(view(1,2,{own}));p.requests[0].resolve({epoch:1,revision:2});await wait();check(!save.disabled,'view before receipt leaves UI locked');
 input.value='99';input.dispatchEvent(new Event('input',{bubbles:true}));p.handle.update(view(1,3,{own:{...own,prediction:{...own.prediction,version:2}}}));check(!p.get('[data-tx-conflict="prediction"]').hidden,'missing same-actor conflict');
 p.get('[data-tx-reload="prediction"]').click();check(input.value==='110','reload did not restore saved answer');check(p.requests.length===1,'reload auto-submitted');
 save.click();p.requests[1].reject(Object.assign(new Error('full'),{code:'queue-full'}));await wait();check(!save.disabled&&input.value==='110','queue refusal lost draft');
 save.click();p.handle.update(view(2,0,{phase:'ready',phase_token:0}));p.requests[2].resolve({epoch:1,revision:4});await wait();check(input.value==='','reset retained old draft');
 p.handle.update(view(2,1));input.value='1';input.dispatchEvent(new Event('input',{bubbles:true}));save.click();p.destroy();p.requests[3].resolve({epoch:2,revision:2});await wait();check(p.container.childElementCount===0,'late receipt revived participant');
 const c=make(controlModule,'presenter'),details=c.get('details');details.open=true;
 const base={control_version:0,count:0,counts:{prediction:{submitted:0,pending:0,unavailable:0},diagnosis:{submitted:0,pending:0,unavailable:0},repair:{submitted:0,pending:0,unavailable:0}},roster:{page:0,pages:1,total:0,rows:[]}};
 c.handle.update(view(1,1,{...base,phase:'ready'}));c.get('[data-tx="advance"]').click();c.handle.update(view(2,0,{...base,phase:'ready'}));c.requests[0].resolve({epoch:1,revision:2});await wait();check(!c.get('[data-tx="advance"]').disabled,'old receipt locked reset controls');
 c.get('[data-tx="advance"]').click();c.destroy();c.requests[1].resolve({epoch:2,revision:1});await wait();check(c.container.childElementCount===0,'late receipt revived controls');
 return ['view-before-receipt','same-actor reload','queue refusal','late reset receipt','disposal'];
},{urls,exercise});};
