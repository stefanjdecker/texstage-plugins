// SPDX-License-Identifier: Apache-2.0
// Installed host/provider: both valid ER models, game points, reveal and reset.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{spawn,spawnSync}=require('node:child_process');
const pw=require('playwright'),family=process.env.BROWSER||'chromium',bundle=path.resolve(process.argv[2]);
const deck=JSON.parse(fs.readFileSync(path.join(bundle,'deck.json'))),de=deck.language?.startsWith('de')||path.basename(bundle).includes('-de');
const output=path.resolve(process.argv[3],de?'de':'en',family);fs.mkdirSync(output,{recursive:true});
const port=Number(process.env.TEXSTAGE_TEST_PORT||18812),base='http://127.0.0.1:'+port;
const server=spawn(process.env.PYTHON||'python',[path.join(__dirname,'serve_lesson.py'),'--bundle',bundle,'--data',fs.mkdtempSync(path.join(output,'profile-')),'--port',String(port)],{windowsHide:true,stdio:['ignore','pipe','pipe']});
const log=fs.createWriteStream(path.join(output,'server.log'));server.stdout.pipe(log);server.stderr.pipe(log);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label){for(let i=0;i<200;i++){if(await fn())return;await delay(100);}throw Error('Timeout: '+label);}
(async()=>{
 let browser;const errors=[],pages=[],history={};
 const watch=(page,role)=>{pages.push(page);history[role]=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('websocket',ws=>ws.on('framereceived',({payload})=>{try{const m=JSON.parse(String(payload));if(m.t==='state')history[role].push(m);}catch{}}));};
 const latest=role=>history[role].at(-1),item=role=>latest(role)?.plugins?.items?.[0];
 const own=role=>item(role)?.views['participant-input']?.data.own;
 const label=(en,german)=>de?german:en;
 try{
  await until(async()=>{try{return(await fetch(base+'/api/status')).ok;}catch{return false;}},'server');
  browser=await pw[family].launch({headless:true});
  const desktop=await browser.newContext({viewport:{width:1440,height:1100}});
  await desktop.addInitScript(()=>localStorage.setItem('texquiz:presenter-key','plugin-demo-key'));
  const presenter=await desktop.newPage();watch(presenter,'presenter');await presenter.goto(base+'/stage?bundle='+deck.bundle);
  const controls=presenter.locator('.presenter-controls'),button=(en,german)=>controls.getByRole('button',{name:label(en,german),exact:true});
  await button('Open answers','Antworten öffnen').waitFor();
  const pin=(await presenter.locator('#pin').innerText()).replace(/\D/g,'');
  const phones=[];
  for(let i=0;i<3;i++){
   const ctx=await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=='firefox'});
   const page=await ctx.newPage();phones.push(page);watch(page,'p'+i);await page.goto(base+'/play?pin='+pin);
   await page.locator('#nick').fill('ER points '+i);await page.locator('#join button[type=submit]').click();await page.locator('.er-lesson textarea').waitFor();
  }
  const maximum=item('p0').public.points;assert(maximum>0,'Use a scored bundle');
  await button('Open answers','Antworten öffnen').click();
  for(const [i,page]of phones.entries()){
   for(const [d,o]of [['person-links','zero-many'],['status-owner',i===2?'person':'registration'],['registration-form',i===1?'entity-pair-key':'relationship']])
    await page.locator('[data-choice="'+d+':'+o+'"]').check();
   await page.getByRole('button',{name:label('Save answer','Antwort speichern'),exact:true}).tap();
  }
  await until(()=>phones.every((_,i)=>own('p'+i)?.status==='saved'),'evaluations');
  for(let i=0;i<3;i++){assert.equal(latest('p'+i).me.score,0);assert.equal(own('p'+i).points,undefined);assert.equal(own('p'+i).feedback,undefined);}
  await button('Close answers','Antworten schließen').click();await button('Reveal alternatives','Alternativen auflösen').click();
  const expected=[maximum,maximum,0];
  await until(()=>expected.every((score,i)=>latest('p'+i).me.score===score&&own('p'+i)?.points===score),'published totals');
  for(const [i,page]of phones.entries()){
   assert.equal(await page.locator('.er-points').innerText(),label('Activity points','Aktivitätspunkte')+': '+expected[i]+' / '+maximum);
   assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),'320px overflow');
  }
  assert(await button('Open answers','Antworten öffnen').isDisabled(),'Scored round must stay closed');
  const downloadPromise=presenter.waitForEvent('download');
  await presenter.getByRole('button',{name:'Results (CSV)',exact:true}).click();
  const download=await downloadPromise,csvPath=path.join(output,'results.csv');await download.saveAs(csvPath);
  const rows=fs.readFileSync(csvPath,'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/).map(line=>line.split(','));
  const header=rows.shift(),nick=header.indexOf('nickname'),scoreColumn=header.indexOf('score'),rankColumn=header.indexOf('rank');
  assert(header.includes('registrations activity points'));
  for(let i=0;i<3;i++){
   const row=rows.find(row=>row[nick]==='ER points '+i);assert(row,'CSV contains each learner');
   assert.equal(Number(row[scoreColumn]),expected[i]);
   assert.equal(Number(row[header.indexOf('registrations activity points')]),expected[i]);
   assert.equal(Number(row[rankColumn]),latest('p'+i).me.rank);
  }
  await phones[0].screenshot({path:path.join(output,'phone-correct.png'),fullPage:true});
  await phones[2].screenshot({path:path.join(output,'phone-incorrect.png'),fullPage:true});
  await presenter.screenshot({path:path.join(output,'presenter.png'),fullPage:true});
  await presenter.locator('#next').click();await controls.waitFor({state:'detached'});
  await presenter.locator('#prev').click();await controls.waitFor();
  await until(()=>expected.every((score,i)=>latest('p'+i).me.score===score&&own('p'+i)?.points===score),'navigation preserves awards');
  let resetMessage='';presenter.once('dialog',async d=>{resetMessage=d.message();await d.accept();});
  await button('Reset activity','Aktivität zurücksetzen').click();
  await until(()=>phones.every((_,i)=>latest('p'+i).me.score===0&&!own('p'+i)),'reset withdraws contribution');
  assert(resetMessage.includes(de?'Punkte':'points'),'Reset explains withdrawal');
  assert(await button('Open answers','Antworten öffnen').isEnabled());
  for(const role of ['p0','p1','p2'])for(const m of history[role])for(const d of m.plugins?.items||[])for(const v of Object.values(d.views)){
   assert(!v.data.participants&&!v.data.selected,'Private inspection never goes to phones');
   if(v.data.phase!=='revealed')assert(!v.data.teaching&&!v.data.own?.feedback&&!Number.isInteger(v.data.own?.points),'No early feedback or points');
  }
  assert.deepEqual(errors,[]);
  const report={browser:family,version:browser.version(),language:de?'de':'en',maximum,awards:expected,bothValidModels:true,incorrectZero:true,hiddenUntilReveal:true,gameTotals:true,csvAndRanks:true,scoredReopenDisabled:true,navigation:true,resetWithdraws:true,viewport:320,errors};
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
 }catch(e){for(const [i,p]of pages.entries())await p.screenshot({path:path.join(output,'failure-'+i+'.png'),fullPage:true}).catch(()=>{});throw e;}
 finally{await browser?.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{if(process.platform==='win32')spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});else server.kill();log.end();});
