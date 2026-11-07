// SPDX-License-Identifier: Apache-2.0
// German deck in English browsers; keyboard controls and a short presenter view.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const {spawn, spawnSync} = require('node:child_process');
const playwright = require('playwright');
const family = process.env.BROWSER || 'chromium', bundle = path.resolve(process.argv[2]);
const root = path.resolve(__dirname, '..'), output = path.join(root,'artifacts','fd-release-ui',family);
fs.mkdirSync(output,{recursive:true});
const profile = fs.mkdtempSync(path.join(output,'profile-'));
const deck = JSON.parse(fs.readFileSync(path.join(bundle,'deck.json')));
assert.equal(deck.language,'de');
const log = fs.createWriteStream(path.join(output,'server.log'));
const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));
let server, browser;
const pages=[], errors=[];
async function until(check,label) {
  for(let n=0;n<200;n++) { if(await check()) return; await delay(100); }
  throw Error('Timed out: '+label);
}
const watch = page => {pages.push(page);page.on('pageerror',e=>errors.push(e.message));return page;};
(async()=>{
  server=spawn(process.env.PYTHON || 'python',[path.join(__dirname,'serve_fd_lesson.py'),
    '--bundle',bundle,'--data',profile],{windowsHide:true,stdio:['ignore','pipe','pipe']});
  server.stdout.pipe(log);server.stderr.pipe(log);
  let startupError;server.on('error',e=>startupError=e);
  await until(()=>{
    if(startupError) throw startupError;
    if(server.exitCode!==null) throw Error('Owned test server exited');
    return fs.existsSync(path.join(profile,'fd-ready.json'));
  },'owned server');
  const base='http://127.0.0.1:'+JSON.parse(fs.readFileSync(path.join(profile,'fd-ready.json'))).port;
  await until(async()=>{try{return(await fetch(base+'/api/status')).ok;}catch{return false;}},'HTTP');
  browser=await playwright[family].launch({headless:true,
    ...(family==='chromium' && process.env.TEXSTAGE_BROWSER_CHANNEL ? {channel:process.env.TEXSTAGE_BROWSER_CHANNEL}: {})});
  const desktop=await browser.newContext({locale:'en-US',viewport:{width:800,height:500}});
  await desktop.addInitScript(()=>localStorage.setItem('texquiz:presenter-key','plugin-demo-key'));
  const presenter=watch(await desktop.newPage());
  await presenter.goto(base+'/stage?bundle='+deck.bundle);
  await presenter.locator('#next').click();
  const controls=presenter.locator('.presenter-controls');
  const open=controls.getByRole('button',{name:'Antworten öffnen',exact:true});
  await open.waitFor(); await open.focus(); await presenter.keyboard.press('Enter');
  await controls.getByRole('button',{name:'Antworten schließen',exact:true}).waitFor();
  const pin=(await presenter.locator('#pin').innerText()).replace(/\D/g,'');
  const mobile=await browser.newContext({locale:'en-US',viewport:{width:320,height:740},hasTouch:true,isMobile:family!=='firefox'});
  const phone=watch(await mobile.newPage());
  await phone.goto(base+'/play?pin='+pin);
  await phone.locator('#nick').fill('Locale test');await phone.locator('#join button[type=submit]').click();
  const button=name=>phone.getByRole('button',{name,exact:true});
  await until(()=>button('Hinzufügen f3').isEnabled(),'open participant editor');
  await button('Hinzufügen f3').tap();await button('Hinzufügen f4').tap();
  for(const name of ['tutor','room','building']) await button('Attribut '+name).tap();
  await button('Antwort speichern').focus();await phone.keyboard.press('Enter');
  await phone.getByText('Antwort gespeichert; Feedback noch nicht freigegeben.',{exact:true}).waitFor();
  const reveal=controls.getByRole('button',{name:'Lösung auflösen',exact:true});
  await reveal.focus();await presenter.keyboard.press('Enter');
  await phone.getByText('Vergebene Punkte: 100 / 100',{exact:true}).waitFor();
  await phone.getByText('Ihr Abschluss und Ihre Herleitung sind korrekt.',{exact:true}).waitFor();
  await controls.getByRole('button',{name:'Herleitung beginnen',exact:true}).scrollIntoViewIfNeeded();
  const presenterBounds=await controls.boundingBox();
  assert(presenterBounds.width>100 && presenterBounds.x>=0 && presenterBounds.x+presenterBounds.width<=801);
  assert(await presenter.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  assert(await phone.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await presenter.screenshot({path:path.join(output,'presenter-800x500.png')});
  await phone.screenshot({path:path.join(output,'phone-german-320.png'),fullPage:true});
  const projector=watch(await desktop.newPage());
  await projector.goto(base+'/stage/projector?bundle='+deck.bundle);
  await projector.locator('.projector-overlay').getByText('Eine mögliche Lösung',{exact:true}).waitFor();
  await projector.screenshot({path:path.join(output,'projector-german.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify({browser:family,version:browser.version(),
    deckLanguage:'de',browserLocale:'en-US',presenterViewport:[800,500],phoneViewport:[320,740],
    keyboardPresenter:true,keyboardSubmission:true,touch:true,language:true,noHorizontalOverflow:true,
    realEvaluation:true,errors},null,2)+'\n');
})().catch(async error=>{
  for(let n=0;n<pages.length;n++) {
    await pages[n].screenshot({path:path.join(output,'failure-'+n+'.png'),fullPage:true}).catch(()=>{});
    fs.writeFileSync(path.join(output,'failure-'+n+'.txt'),await pages[n].locator('body').innerText().catch(()=>''));
  }
  console.error(error);process.exitCode=1;
}).finally(async()=>{
  await browser?.close();
  if(server?.pid) {
    if(process.platform==='win32') spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});
    else server.kill();
  }
  log.end();
});
