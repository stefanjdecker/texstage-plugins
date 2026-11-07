// SPDX-License-Identifier: Apache-2.0
// Actual installed host, installed provider, role-filtered sockets and worker CSP.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const {spawn, spawnSync} = require("node:child_process");
const playwright = require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(__dirname, ".."), bundle = path.resolve(process.argv[2]);
const family = process.env.BROWSER || "chromium";
const output = path.join(root, "artifacts", "relational-lesson", family);
fs.mkdirSync(output, {recursive:true});
const profile = fs.mkdtempSync(path.join(output, "profile-")), port = Number(process.env.TEXSTAGE_TEST_PORT || 18749);
const base = "http://127.0.0.1:" + port, deck = JSON.parse(fs.readFileSync(path.join(bundle, "deck.json")));
const source = mode => JSON.parse(fs.readFileSync(path.join(root, "examples/relational/activities/" + mode + ".json")));
const server = spawn(process.env.PYTHON || "python", [path.join(__dirname, "serve_lesson.py"),
  "--bundle", bundle, "--data", profile, "--port", String(port)], {windowsHide:true,stdio:["ignore","pipe","pipe"]});
const log = fs.createWriteStream(path.join(output, "server.log")); server.stdout.pipe(log); server.stderr.pipe(log);
const delay = ms => new Promise(r => setTimeout(r, ms));
async function until(check, label) {
  for (let i=0;i<100;i++) { if (await check()) return; await delay(100); }
  throw new Error("Timed out: " + label);
}
(async () => {
  let browser;
  const errors = [], sockets = {phone:[],projector:[]}, pages = [];
  try {
    await until(async () => { try { return (await fetch(base+"/api/status")).ok; } catch { return false; } }, "server");
    browser = await playwright[family].launch({headless:true,
      ...(process.env.TEXSTAGE_BROWSER_CHANNEL ? {channel:process.env.TEXSTAGE_BROWSER_CHANNEL} : {})});
    const desktop = await browser.newContext({viewport:{width:1440,height:1100}});
    await desktop.addInitScript(() => localStorage.setItem("texquiz:presenter-key","plugin-demo-key"));
    const watch = (page, role) => {
      pages.push(page); page.on("pageerror", e => errors.push(e.message));
      if (sockets[role]) page.on("websocket", socket => socket.on("framereceived", ({payload}) => {
        try { const m = JSON.parse(String(payload)); if (m.t === "state") sockets[role].push(m); } catch {}
      }));
    };
    const presenter = await desktop.newPage(); watch(presenter);
    await presenter.goto(base+"/stage?bundle="+deck.bundle);
    await presenter.locator("#next").click();
    const controls = presenter.locator(".presenter-controls");
    await controls.getByRole("button",{name:"Open answers",exact:true}).waitFor();
    const pin = (await presenter.locator("#pin").innerText()).replace(/\D/g,"");
    const projector = await desktop.newPage(); watch(projector,"projector");
    await projector.goto(base+"/stage/projector?bundle="+deck.bundle);
    const mobile = await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=="firefox"});
    const phone = await mobile.newPage(); watch(phone,"phone");
    await phone.goto(base+"/play?pin="+pin);
    await phone.locator("#nick").fill("Test learner"); await phone.locator("#join button[type=submit]").click();
    const input = phone.getByLabel("Answer as JSON");
    await input.waitFor();
    assert(await phone.getByRole("button",{name:"Save answer",exact:true}).isDisabled());
    const starter = await input.inputValue();
    await controls.getByRole("button",{name:"Open answers",exact:true}).click();
    // Invalid JSON is a local error; it never creates an authoritative grade.
    await input.fill("{broken");
    await phone.getByRole("button",{name:"Save answer",exact:true}).click();
    await phone.getByRole("alert").filter({hasText:"Invalid answer format"}).waitFor();
    const answer = JSON.stringify(source("construct").worked_answer,null,2);
    await input.fill(answer);
    // Same actor on a second device. An unrelated update must preserve this draft and focus.
    const otherContext = await browser.newContext({storageState:await mobile.storageState(),viewport:{width:390,height:844}});
    const other = await otherContext.newPage(); watch(other);
    await other.goto(base+"/play?pin="+pin);
    await other.getByLabel("Answer as JSON").waitFor();
    await input.focus();
    await controls.getByRole("button",{name:"Inspect an answer privately",exact:true}).click();
    assert.equal(await input.inputValue(),answer);
    assert(await input.evaluate(node => node === document.activeElement));
    await other.getByLabel("Answer as JSON").fill(answer);
    await other.getByRole("button",{name:"Save answer",exact:true}).click();
    await phone.getByRole("button",{name:"Keep my draft",exact:true}).waitFor();
    assert.equal(await input.inputValue(),answer);
    await phone.getByRole("button",{name:"Keep my draft",exact:true}).click();
    await input.focus(); await phone.keyboard.press("Tab");
    assert.equal(await phone.evaluate(() => document.activeElement.textContent),"Save answer");
    await phone.keyboard.press("Enter");
    await until(async () => (await controls.innerText()).includes("0 / 1 / 0 / 0"), "authoritative worker result");
    assert.equal(await phone.getByText("The answer passes the configured checks.",{exact:true}).count(),0);
    const latest = role => sockets[role].at(-1).plugins.items[0];
    for (const role of ["phone","projector"]) {
      const d = latest(role), v = Object.values(d.views)[0].data;
      assert(!v.worked && !v.demonstration && !v.own?.feedback);
      const serialized = JSON.stringify(d);
      assert(!serialized.includes('"private":') && !serialized.includes('"expected":') && !serialized.includes('"fixtures":'));
    }
    await controls.getByRole("button",{name:"Close answers",exact:true}).click();
    await until(() => phone.getByRole("button",{name:"Save answer",exact:true}).isDisabled(), "closed submissions");
    const select = controls.getByLabel("Inspect an answer privately");
    await select.selectOption({index:1});
    await controls.getByRole("button",{name:"Inspect an answer privately",exact:true}).click();
    await controls.getByText(/The answer passes the configured checks/).waitFor();
    await controls.getByRole("button",{name:"Share selected answer anonymously",exact:true}).click();
    await projector.getByText("Anonymously shared answer",{exact:true}).waitFor();
    assert(!JSON.stringify(latest("projector")).includes("Test learner"));
    await controls.getByRole("button",{name:"Clear shared answer",exact:true}).click();
    await controls.getByRole("button",{name:"Reveal solution",exact:true}).click();
    await phone.getByText(/The answer passes the configured checks/).waitFor();
    await phone.getByText("One worked answer",{exact:true}).click();
    assert.equal(await input.inputValue(),answer);
    const overflow = await phone.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
    assert(!overflow,"320-pixel phone layout overflows");
    for (const [name,page] of [["phone",phone],["presenter",presenter],["projector",projector]])
      await page.screenshot({path:path.join(output,name+".png"),fullPage:true});
    // Reset while editing must explicitly resolve the obsolete draft.
    await input.fill(answer + "\n ");
    presenter.once("dialog", dialog => dialog.accept());
    await controls.getByRole("button",{name:"Reset activity",exact:true}).click();
    await phone.getByRole("button",{name:"Reload saved answer",exact:true}).waitFor();
    await phone.getByRole("button",{name:"Reload saved answer",exact:true}).click();
    assert.equal(await input.inputValue(),starter);
    // Both modes, actual navigation teardown and newly mounted draft.
    await presenter.locator("#next").click();
    await phone.getByRole("heading",{name:"Move filters earlier",exact:true}).waitFor();
    await controls.getByRole("button",{name:"Open answers",exact:true}).click();
    await input.fill(JSON.stringify(source("rewrite").worked_answer,null,2));
    await phone.getByRole("button",{name:"Save answer",exact:true}).tap();
    await until(async () => (await controls.innerText()).includes("0 / 1 / 0 / 0"), "rewrite certificate result");
    await controls.getByRole("button",{name:"Close answers",exact:true}).click();
    await controls.getByRole("button",{name:"Reveal solution",exact:true}).click();
    await phone.getByText(/The answer passes the configured checks/).waitFor();
    await presenter.locator("#next").click();
    await phone.locator(".participant-input").waitFor({state:"detached"});
    await presenter.locator(".presenter-controls").waitFor({state:"detached"});
    assert.deepEqual(errors,[]);
    const report = {browser:family,version:browser.version(),modes:["construct","rewrite"],viewport:320,
      realWorker:true,privacy:true,draftAndFocus:true,keyboard:true,touch:true,sameActorConflict:true,sharing:true,reset:true,teardown:true,errors};
    fs.writeFileSync(path.join(output,"report.json"),JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify(report));
  } catch (error) {
    for (let i=0;i<pages.length;i++) {
      await pages[i].screenshot({path:path.join(output,"failure-"+i+".png"),fullPage:true}).catch(()=>{});
      fs.writeFileSync(path.join(output,"failure-"+i+".txt"),await pages[i].locator("body").innerText().catch(()=>""));
    }
    console.error("Browser errors:",errors);
    throw error;
  } finally { await browser?.close(); }
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(()=>{
  if (server.pid && process.platform === "win32")
    spawnSync("taskkill",["/PID",String(server.pid),"/T","/F"],{windowsHide:true,stdio:"ignore"});
  else server.kill();
  log.end();
});

