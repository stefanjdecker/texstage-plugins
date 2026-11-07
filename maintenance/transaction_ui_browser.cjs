// SPDX-License-Identifier: Apache-2.0
// Installed-wheel lesson: authenticated host, real evaluator and native UI controls.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{spawn}=require('node:child_process');
const pw=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||'playwright');
const lifecycle=require('./transaction_ui_lifecycle.cjs');
const bundle=path.resolve(process.argv[2]),family=process.env.BROWSER||'chromium',language=process.env.TRANSACTION_LANGUAGE||'en';
const output=path.resolve(process.argv[3]||'artifacts/transactions-ui',family+'-'+language);fs.mkdirSync(output,{recursive:true});
const deck=JSON.parse(fs.readFileSync(path.join(bundle,'deck.json'))),profile=fs.mkdtempSync(path.join(output,'profile-'));
const TYPE='io.github.stefanjdecker.transactionactivity.schedule',keys=JSON.parse(fs.readFileSync(path.join(bundle,'keys.json')));
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label){for(let i=0;i<300;i++){if(await fn())return;await delay(100);}throw Error('Timeout: '+label);}
async function port(){const s=require('node:net').createServer();return new Promise((resolve,reject)=>{s.once('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(e=>e?reject(e):resolve(p));});});}
function instrumentation(){const Native=window.WebSocket;window.transactionUIState=null;window.WebSocket=class extends Native{constructor(...args){super(...args);this.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.t==='state')window.transactionUIState=m;});}};}
let item='counter';
async function data(page){return page.evaluate(item=>{const d=window.transactionUIState?.plugins?.items?.find(d=>d.item===item);return d&&(d.views['presenter-controls']||Object.values(d.views)[0])?.data;},item);}
const action=(p,name)=>p.locator('[data-tx="'+name+'"]');
async function click(p,name){await action(p,name).click();}
async function panel(p){const details=p.locator('.tx-controls>details');await details.waitFor();if(!await details.evaluate(n=>n.open))await details.locator('summary').click();}
async function phase(p,phone,value){await action(p,'advance').focus();await action(p,'advance').press('Space');await until(async()=>(await data(phone))?.phase===value,'phase '+value);await until(()=>action(p,'advance').isEnabled().then(x=>x||value==='reveal'),'control receipt');}
async function prediction(p,values){for(const [k,v]of Object.entries(values))await p.locator('[data-tx-value="'+k+'"]').fill(String(v));}
async function diagnosis(p,answer){for(const edge of answer.edges){const id=edge.from+'-'+edge.to;await p.locator('[data-tx-edge="'+id+'"]').check();for(let i=0;i<2;i++)await p.locator('[data-tx-witness="'+id+'-'+i+'"]').selectOption(edge.witness[i]);}
 await action(p,'certificate-kind').selectOption(answer.certificate.kind);for(const [i,v]of answer.certificate.vertices.entries())await p.locator('[data-tx-vertex="'+i+'"]').selectOption(v);
}
async function repair(p,order){for(let target=0;target<order.length;target++){const id=order[target];for(let i=0;i<20;i++){const ids=await p.locator('[data-tx-op]').evaluateAll(ns=>ns.map(n=>n.dataset.txOp));const pos=ids.indexOf(id);if(pos===target)break;assert(pos>target);await p.locator('[data-tx-op="'+id+'"] [data-tx-move="up"]').click();}}}
async function saved(p,name,version){await until(async()=>{const own=(await data(p))?.own?.[name];return own?.version===version&&own.status==='saved';},'saved '+name+' '+version);}
async function submit(p,name){await p.locator('[data-tx-submit="'+name+'"]').click();}
async function geometry(p){const g=await p.evaluate(()=>{const r=document.querySelector('.tx-participant');return{width:document.documentElement.scrollWidth,viewport:innerWidth,unlabeled:[...r.querySelectorAll('input,select')].filter(n=>!n.labels?.length&&!n.getAttribute('aria-label')).length,minTouch:Math.min(...[...r.querySelectorAll('button')].filter(n=>n.getClientRects().length).map(n=>n.getBoundingClientRect().height))};});assert(g.width<=g.viewport+1,JSON.stringify(g));assert.equal(g.unlabeled,0);assert(g.minTouch>=43);return g;}
let server,log;
(async()=>{let browser;const errors=[],timings=[],modules={};try{
 const base='http://127.0.0.1:'+await port();server=spawn(process.env.PYTHON||'python',[path.join(__dirname,'serve_lesson.py'),'--bundle',bundle,'--data',profile,'--port',new URL(base).port],{windowsHide:true});
 log=fs.createWriteStream(path.join(output,'server.log'));server.stdout.pipe(log);server.stderr.pipe(log);
 await until(()=>{if(server.exitCode!==null)throw Error('Server exited');return fetch(base+'/api/status').then(r=>r.ok).catch(()=>false);},'server');
 browser=await pw[family].launch({headless:true});
 async function context(options={}){const c=await browser.newContext({locale:language,reducedMotion:'reduce',...options});await c.addInitScript(instrumentation);return c;}
 function watch(p){p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{for(const [key,file]of Object.entries({participant:'participant.mjs',controls:'presenter-controls.mjs'}))if(r.url().endsWith('/texstage_transaction_activity/web/'+file))modules[key]=r.url();});return p;}
 const desktop=await context({viewport:{width:1440,height:1000}});await desktop.addInitScript(()=>localStorage.setItem('texquiz:presenter-key','plugin-demo-key'));
 const presenter=watch(await desktop.newPage());await presenter.goto(base+'/stage?bundle='+deck.bundle);await presenter.locator('#next').click();await until(async()=>!!await data(presenter),'first activity');
 const projector=watch(await desktop.newPage());await projector.goto(base+'/stage/projector?bundle='+deck.bundle);
 const pin=(await presenter.locator('#pin').innerText()).replace(/\D/g,'');
 const mobile=await context({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=='firefox'});
 async function join(context,nick){const p=watch(await context.newPage());await p.goto(base+'/play?pin='+pin);if(await p.locator('#join').isVisible()){await p.locator('#nick').fill(nick);await p.locator('#join button[type=submit]').click();}await p.locator('.tx-participant').waitFor();return p;}
 const phone=await join(mobile,'Alice'),same=await context({storageState:await mobile.storageState(),viewport:{width:390,height:844}}),second=await join(same,'Alice');
 const bob=await join(await context({viewport:{width:390,height:844}}),'Bob');
 for(const name of ['counter','independent','read_read','write_write','chain','blind_write']){
  console.log(family+'/'+language+': '+name);if(name!==item){await presenter.locator('#next').click();item=name;}
  await until(async()=>!!await data(phone)&&!!await data(presenter)&&!!await data(bob),'item '+item);await panel(presenter);
  const worked=keys.items[TYPE][item].private.worked;
  assert(!(await data(phone)).worked);await phase(presenter,phone,'predict');
  await prediction(phone,worked.original.final);const input=phone.locator('[data-tx-value]').first();await input.focus();const value=await input.inputValue();
  await prediction(bob,Object.fromEntries(Object.keys(worked.original.final).map(k=>[k,0])));await submit(bob,'prediction');await saved(bob,'prediction',1);
  assert.equal(await input.inputValue(),value);assert(await input.evaluate(n=>document.activeElement===n),'peer update stole focus');assert(!(await data(phone)).own);
  if(name==='counter')await prediction(second,Object.fromEntries(Object.keys(worked.original.final).map(k=>[k,99])));
  await submit(phone,'prediction');await saved(phone,'prediction',1);assert(!(await data(phone)).own.prediction.feedback);
  if(name==='counter'){
   await second.locator('[data-tx-conflict="prediction"]').waitFor({state:'visible'});await second.locator('[data-tx-keep="prediction"]').click();await submit(second,'prediction');await saved(second,'prediction',2);
   await prediction(phone,worked.original.final);await submit(phone,'prediction');await saved(phone,'prediction',3);
   await geometry(phone);await phone.setViewportSize({width:640,height:360});await geometry(phone);await phone.setViewportSize({width:320,height:740});await phone.screenshot({path:path.join(output,'phone-predict.png'),fullPage:true});
  }
  await phase(presenter,phone,'inspect');assert(!(await data(phone)).own.prediction.feedback);assert(!(await data(phone)).worked);
  await action(presenter,'cursor').selectOption('2');await until(async()=>(await data(phone)).cursor===2,'shared cursor');
  if(name==='counter'){await projector.screenshot({path:path.join(output,'projector-inspect.png')});await presenter.screenshot({path:path.join(output,'presenter-inspect.png')});}
  await action(presenter,'cursor').selectOption(String(keys.items[TYPE][item].private.original.order.length));await until(async()=>!!(await data(phone))?.own.prediction.feedback,'prediction release');assert((await data(phone)).own.prediction.feedback.correct);
  await phase(presenter,phone,'diagnose');await diagnosis(phone,worked.original.diagnosis);await submit(phone,'diagnosis');await saved(phone,'diagnosis',1);assert(!(await data(phone)).own.diagnosis.feedback);
  await phase(presenter,phone,'repair');await repair(phone,worked.repairs[0].order);await geometry(phone);
  const start=performance.now();await submit(phone,'repair');await saved(phone,'repair',1);timings.push({item,repairMs:Math.round(performance.now()-start)});assert(!(await data(phone)).own.repair.feedback);
  if(name==='counter'){
   await phone.screenshot({path:path.join(output,'phone-repair.png'),fullPage:true});
   await presenter.locator('#prev').click();await presenter.locator('#next').click();await until(async()=>(await data(phone))?.paused,'return paused');await panel(presenter);await click(presenter,'resume');await until(async()=>!(await data(phone))?.paused,'resume');
  }
  await phase(presenter,phone,'reveal');const own=(await data(phone)).own;assert(own.diagnosis.feedback.correct);assert(own.repair.feedback.correct);assert((await data(phone)).worked);
  const roster=(await data(presenter)).roster.rows;const student=roster.find(r=>r.summary.repair==='saved');assert(student);await action(presenter,'roster').selectOption(student.actor);await click(presenter,'select');await until(async()=>(await data(presenter))?.selected?.actor===student.actor,'private selection');
  assert(!(await data(projector)).selected);await click(presenter,'share');await until(async()=>!!(await data(projector))?.shared,'anonymous share');assert(!JSON.stringify((await data(projector)).shared).includes(student.actor));
  const shared=action(projector,'shared-answer');await shared.waitFor({state:'visible'});assert(await shared.evaluate(n=>{const box=n.closest('.tx-overlay').getBoundingClientRect(),r=n.getBoundingClientRect();return r.top>=box.top&&r.top<box.bottom-40;}),'shared answer is below the projector viewport');
  const session=await presenter.evaluate(()=>window.transactionUIState.session.id);const sid=typeof session==='string'?session:await presenter.evaluate(()=>window.transactionUIState.session.session);
  // Read the session from the state descriptor used by the HTTP archive route.
  if(name==='counter'){
   await phone.screenshot({path:path.join(output,'phone-reveal.png'),fullPage:true});await projector.screenshot({path:path.join(output,'projector-reveal.png')});
   fs.writeFileSync(path.join(output,'phone-aria.yml'),await phone.locator('.tx-participant').ariaSnapshot());
  }
  await click(presenter,'clear-share');await until(async()=>!(await data(projector))?.shared,'clear share');
  if(name==='counter'){await until(()=>projector.locator('.tx-worked .tx-card').count().then(n=>n===3),'worked repairs restored');assert(await projector.locator('.tx-worked .tx-card').last().evaluate(n=>n.getBoundingClientRect().bottom<=n.closest('.tx-overlay').getBoundingClientRect().bottom+1),'worked repair clipped on projector');await projector.screenshot({path:path.join(output,'projector-worked.png')});}
  if(name==='blind_write'){await click(presenter,'reset');await click(presenter,'confirm-reset');await until(async()=>(await data(phone))?.phase==='ready','reset');assert(!(await data(phone)).own);}
 }
 const controlled=await lifecycle(phone,modules,JSON.parse(keys.items[TYPE].counter.evaluations.analysis.seed));
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(output,'report.json'),JSON.stringify({family,language,browser:browser.version(),timings,errors,controlled,checks:['six lessons','all phases','independent evaluator','peer focus','two-device keep','pause/resume','anonymous sharing','epoch reset','320px geometry','native labels','synthetic screenshots']},null,2));
 console.log('PASS '+family+'/'+language);
 }finally{if(browser)await browser.close();if(server){server.kill();await new Promise(resolve=>{if(server.exitCode!==null)resolve();else server.once('exit',resolve);});}if(log)await new Promise(r=>log.end(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
