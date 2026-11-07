// SPDX-License-Identifier: Apache-2.0
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),{spawn,spawnSync}=require("node:child_process");
const pw=require("playwright"),family=process.env.BROWSER||"chromium",bundle=path.resolve(process.argv[2]);
const output=path.resolve(process.argv[3],family);fs.mkdirSync(output,{recursive:true});
const port=Number(process.env.TEXSTAGE_TEST_PORT||18795),base="http://127.0.0.1:"+port;
const deck=JSON.parse(fs.readFileSync(path.join(bundle,"deck.json")));
const server=spawn(process.env.PYTHON||"python",[path.join(__dirname,"serve_lesson.py"),"--bundle",bundle,
 "--data",fs.mkdtempSync(path.join(output,"profile-")),"--port",String(port)],{windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log=fs.createWriteStream(path.join(output,"server.log"));server.stdout.pipe(log);server.stderr.pipe(log);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){for(let i=0;i<150;i++){if(await fn())return;await delay(100);}throw Error("German UI timeout");}
(async()=>{
 let browser;const errors=[],pages=[];
 try{
  await until(async()=>{try{return(await fetch(base+"/api/status")).ok;}catch{return false;}});
  browser=await pw[family].launch({headless:true});const desktop=await browser.newContext({viewport:{width:1440,height:1100}});
  await desktop.addInitScript(()=>localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
  const presenter=await desktop.newPage();pages.push(presenter);presenter.on("pageerror",e=>errors.push(e.message));
  await presenter.goto(base+"/stage?bundle="+deck.bundle);
  const controls=presenter.locator(".presenter-controls");
  await controls.getByRole("button",{name:"Antworten öffnen",exact:true}).click();
  const pin=(await presenter.locator("#pin").innerText()).replace(/\D/g,"");
  const mobile=await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
  const phone=await mobile.newPage();pages.push(phone);phone.on("pageerror",e=>errors.push(e.message));
  await phone.goto(base+"/play?pin="+pin);await phone.locator("#nick").fill("Deutsch");
  await phone.locator("#join button[type=submit]").click();await phone.locator(".er-lesson textarea").waitFor();
  const expected=deck.items["io.github.stefanjdecker.erdecisions.lesson"].registrations.requirements;
  for(const r of expected)await phone.getByText(r.text.de,{exact:true}).waitFor();
  const text=await phone.locator(".er-lesson").innerText();
  assert(text.includes("höchstens")&&text.includes("unabhängig"),"Native phone Unicode must survive transport");
  for(const [d,o]of [["person-links","zero-many"],["status-owner","registration"],["registration-form","entity-pair-key"]])
    await phone.locator('[data-choice="'+d+":"+o+'"]').check();
  const input=phone.locator(".er-lesson textarea");await input.fill("Jede Anmeldung erhält ihren eigenen Status. 😊");
  await phone.getByRole("button",{name:"Modell ansehen",exact:true}).tap();
  await phone.getByText("Jede einzelne Entität Person nimmt an 0..* Verknüpfungen teil.",{exact:true}).waitFor();
  await phone.getByRole("button",{name:"Zurück zu den Entscheidungen",exact:true}).tap();
  await until(()=>phone.getByRole("button",{name:"Antwort speichern",exact:true}).isEnabled());
  await phone.getByRole("button",{name:"Antwort speichern",exact:true}).tap();
  await until(async()=>(await controls.innerText()).includes("0 / 1 / 0 / 0"));
  await controls.getByRole("button",{name:"Antworten schließen",exact:true}).click();
  await controls.getByRole("button",{name:"Alternativen auflösen",exact:true}).click();
  await phone.getByText("Dieses Modell besteht die konfigurierten Beispiele.",{exact:true}).waitFor();
  assert.equal(await input.inputValue(),"Jede Anmeldung erhält ihren eigenen Status. 😊");
  await phone.screenshot({path:path.join(output,"phone.png"),fullPage:true});
  await presenter.screenshot({path:path.join(output,"presenter.png"),fullPage:true});
  assert.deepEqual(errors,[]);
  const report={browser:family,version:browser.version(),language:"de",viewport:320,nativeUnicode:true,nonBmpRationale:true,submitReveal:true,errors};
  fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify(report));
 }catch(error){
  for(const [i,p]of pages.entries())await p.screenshot({path:path.join(output,"failure-"+i+".png"),fullPage:true}).catch(()=>{});
  throw error;
 }finally{await browser?.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{if(process.platform==="win32")spawnSync("taskkill",["/PID",String(server.pid),"/T","/F"],{windowsHide:true,stdio:"ignore"});else server.kill();log.end();});

