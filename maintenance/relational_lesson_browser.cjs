// SPDX-License-Identifier: Apache-2.0
// Installed-wheel visual editor, authenticated host, actual evaluator and unchanged CSP.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {spawn,spawnSync}=require('node:child_process'),pw=require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE||'playwright');
const {actions}=require('./relational_editor_actions.cjs');
const root=path.resolve(__dirname,'..'),bundle=path.resolve(process.argv[2]),family=process.env.BROWSER||'chromium',language=process.env.RELATIONAL_LANGUAGE||'en';
const output=path.resolve(process.argv[3]||path.join(root,'artifacts/relational-lesson',family,language));fs.mkdirSync(output,{recursive:true});
const deck=JSON.parse(fs.readFileSync(path.join(bundle,'deck.json'))),source=mode=>JSON.parse(fs.readFileSync(path.join(root,'examples/relational/activities',mode+'.json')));
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(check,label,ms=20000){const start=Date.now();while(Date.now()-start<ms){if(await check())return;await delay(100);}throw Error('Timed out: '+label);}
async function freePort(){const server=require('node:net').createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port;await new Promise(r=>server.close(r));return port;}
(async()=>{
 let server,browser,log;const errors=[],pages=[],states={phone:[],projector:[]},timings=[];
 try{
  const result=spawnSync(process.env.PYTHON||'python',['-c','import pathlib,texstage_relational_lab;print(pathlib.Path(texstage_relational_lab.__file__).parent)'],{encoding:'utf8',windowsHide:true});assert.equal(result.status,0,result.stderr);
  const packageRoot=result.stdout.trim(),ui=await import(pathToFileURL(path.join(packageRoot,'web/lesson-ui.mjs'))),{editorWords}=await import(pathToFileURL(path.join(packageRoot,'web/editor-text.mjs')));
  const w=ui.words(language),e=editorWords(language),port=await freePort(),base='http://127.0.0.1:'+port;
  server=spawn(process.env.PYTHON||'python',[path.join(__dirname,'serve_lesson.py'),'--bundle',bundle,'--data',fs.mkdtempSync(path.join(output,'profile-')),'--port',String(port)],{windowsHide:true,stdio:['ignore','pipe','pipe']});
  log=fs.createWriteStream(path.join(output,'server.log'));server.stdout.pipe(log);server.stderr.pipe(log);
  await until(()=>fetch(base+'/api/status').then(r=>r.ok).catch(()=>false),'server');
  browser=await pw[family].launch({headless:true});
  const desktop=await browser.newContext({viewport:{width:1440,height:1100},reducedMotion:'reduce'});await desktop.addInitScript(()=>localStorage.setItem('texquiz:presenter-key','plugin-demo-key'));
  const watch=(page,role)=>{pages.push(page);page.on('pageerror',e=>errors.push(e.message));if(states[role])page.on('websocket',s=>s.on('framereceived',({payload})=>{try{const m=JSON.parse(String(payload));if(m.t==='state')states[role].push(m);}catch{}}));};
  const presenter=await desktop.newPage();watch(presenter);await presenter.goto(base+'/stage?bundle='+deck.bundle);await presenter.locator('#next').click();
  const controls=presenter.locator('.presenter-controls');await controls.getByRole('button',{name:w.openButton,exact:true}).waitFor();
  const pin=(await presenter.locator('#pin').innerText()).replace(/\D/g,'');
  const projector=await desktop.newPage();watch(projector,'projector');await projector.goto(base+'/stage/projector?bundle='+deck.bundle);
  const mobile=await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=='firefox',reducedMotion:'reduce'});
  const phone=await mobile.newPage();watch(phone,'phone');await phone.goto(base+'/play?pin='+pin);await phone.locator('#nick').fill('Synthetic learner');await phone.locator('#join button[type=submit]').click();
  const a=actions(phone,e),save=phone.getByRole('button',{name:w.save,exact:true});await a.editor.waitFor();assert.equal(await phone.locator('.participant-input textarea').count(),0);assert(await save.isDisabled());
  await controls.getByRole('button',{name:w.openButton,exact:true}).click();
  await a.controls(save);
  const started=Date.now();await a.construction();await a.inspect();await until(()=>a.editor.locator('.rl-preview').innerText().then(t=>t.includes('Ada')),'intermediate result');timings.push({mode:'construct',interactionMs:Date.now()-started});await a.edit();
  assert(!(await save.isDisabled()));
  // An unrelated revision preserves a partly edited field and focus.
  await a.select([0,0,0]);
  const draft=a.form.getByLabel(e.right+' · '+e.value,{exact:true});await draft.fill('draft');await draft.focus();
  await controls.getByRole('button',{name:w.inspect,exact:true}).click();assert.equal(await draft.inputValue(),'draft');assert(await draft.evaluate(n=>n===document.activeElement));assert(await save.isDisabled());
  await a.form.getByRole('button',{name:e.discard,exact:true}).click();await a.select([]);
  // A second device changes the saved answer while the first keeps its query.
  const secondContext=await browser.newContext({storageState:await mobile.storageState(),viewport:{width:390,height:844}}),other=await secondContext.newPage();watch(other);
  await other.goto(base+'/play?pin='+pin);const b=actions(other,e);await b.editor.waitFor();await b.start();await other.getByRole('button',{name:w.save,exact:true}).click();
  await phone.getByRole('button',{name:w.keep,exact:true}).waitFor();await phone.getByRole('button',{name:w.keep,exact:true}).click();
  await save.focus();await phone.keyboard.press('Enter');
  await until(async()=> (await controls.innerText()).includes('0 / 1 / 0 / 0'),'authoritative correct construction');
  const latest=role=>states[role].at(-1).plugins.items[0];
  for(const role of ['phone','projector']){const d=latest(role),v=Object.values(d.views)[0].data;assert(!v.worked&&!v.demonstration&&!v.own?.feedback);const raw=JSON.stringify(d);assert(!raw.includes('"private":')&&!raw.includes('"expected":')&&!raw.includes('"fixtures":'));}
  const own=latest('phone').views['participant-input'].data.own;assert.deepEqual(own.answer,source('construct').worked_answer);
  assert.equal(await phone.getByText(w.checked,{exact:true}).count(),0);
  await a.inspect();await phone.screenshot({path:path.join(output,'phone-builder.png'),fullPage:true});await a.edit();
  await controls.getByRole('button',{name:w.closeButton,exact:true}).click();await until(()=>save.isDisabled(),'closed');
  await controls.getByLabel(w.inspect,{exact:true}).selectOption({index:1});await controls.getByRole('button',{name:w.inspect,exact:true}).click();
  await controls.getByText(new RegExp(w.checked.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))).waitFor();await controls.getByRole('button',{name:w.share,exact:true}).click();
  await projector.getByText(w.shared,{exact:true}).waitFor();assert(!JSON.stringify(latest('projector')).includes('Synthetic learner'));
  await projector.screenshot({path:path.join(output,'projector-shared.png'),fullPage:true});
  await controls.getByRole('button',{name:w.clear,exact:true}).click();await controls.getByRole('button',{name:w.reveal,exact:true}).click();await phone.getByText(new RegExp(w.checked.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))).waitFor();
  await phone.getByText(w.worked,{exact:true}).click();assert.equal(await phone.locator('.participant-input textarea').count(),0);
  assert(!(await phone.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),'320px overflow');
  await phone.setViewportSize({width:740,height:320});assert(!(await phone.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),'landscape overflow');await phone.setViewportSize({width:320,height:740});
  await phone.screenshot({path:path.join(output,'phone-reveal.png'),fullPage:true});await presenter.screenshot({path:path.join(output,'presenter.png'),fullPage:true});
  // Reset preserves an obsolete draft until the participant explicitly reloads.
  await a.select([0,0,0]);await a.form.getByLabel(e.right+' · '+e.value,{exact:true}).fill('old draft');presenter.once('dialog',d=>d.accept());await controls.getByRole('button',{name:w.reset,exact:true}).click();
  await phone.getByRole('button',{name:w.reload,exact:true}).waitFor();await phone.getByRole('button',{name:w.reload,exact:true}).click();await a.form.getByRole('button',{name:e.addTable,exact:true}).waitFor();
  await presenter.locator('#next').click();await phone.getByRole('heading',{name:source('rewrite').exercise.title[language],exact:true}).waitFor();
  await controls.getByRole('button',{name:w.openButton,exact:true}).click();const begin=Date.now();await a.rewrite(source('rewrite').worked_answer.steps);timings.push({mode:'rewrite',interactionMs:Date.now()-begin});
  await a.editor.getByRole('button',{name:e.undo,exact:true}).click();await a.editor.getByRole('button',{name:e.redo,exact:true}).click();
  await save.tap();await until(async()=> (await controls.innerText()).includes('0 / 1 / 0 / 0'),'authoritative rewrite');
  await phone.screenshot({path:path.join(output,'phone-rewrite.png'),fullPage:true});
  await controls.getByRole('button',{name:w.closeButton,exact:true}).click();await controls.getByRole('button',{name:w.reveal,exact:true}).click();
  await phone.getByText(new RegExp(w.checked.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))).waitFor();
  await projector.screenshot({path:path.join(output,'projector-rewrite.png'),fullPage:true});
  await presenter.locator('#next').click();await phone.locator('.participant-input').waitFor({state:'detached'});assert.deepEqual(errors,[]);
  const report={family,language,browser:browser.version(),timings,checks:['native construction','all eight operators','typed predicates','invalid integer','empty projection','header mismatch and repair','empty preview','branch removal and undo','intermediate result','no JSON input','actual authoritative evaluator','privacy before reveal','draft/focus','same-actor keep','epoch reload','anonymous sharing','rewrite rule controls','undo/redo','keyboard save','touch save','320px','landscape','reduced motion','teardown'],errors};
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }catch(error){for(const [i,p]of pages.entries()){await p.screenshot({path:path.join(output,'failure-'+i+'.png'),fullPage:true}).catch(()=>{});fs.writeFileSync(path.join(output,'failure-'+i+'.txt'),await p.locator('body').innerText().catch(()=>''));}console.error(errors);throw error;}
 finally{await browser?.close();if(server?.pid){if(process.platform==='win32')spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});else server.kill();}log?.end();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
