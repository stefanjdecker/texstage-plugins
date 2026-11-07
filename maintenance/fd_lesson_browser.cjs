// SPDX-License-Identifier: Apache-2.0
// Actual installed host, installed provider, role-filtered sockets and worker CSP.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const {spawn, spawnSync} = require("node:child_process");
const playwright = require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE || "playwright");
const root = path.resolve(__dirname, ".."), bundle = path.resolve(process.argv[2]);
const family = process.env.BROWSER || "chromium";
const output = path.join(root, "artifacts", "fd-lesson", family);
fs.mkdirSync(output, {recursive:true});
const profile = fs.mkdtempSync(path.join(output, "profile-")), port = Number(process.env.TEXSTAGE_TEST_PORT || 0);
const deck = JSON.parse(fs.readFileSync(path.join(bundle, "deck.json")));
let base, server;
const source = mode => JSON.parse(fs.readFileSync(path.join(root, "examples/functional-dependencies/activities/" + mode + ".json")));
const log = fs.createWriteStream(path.join(output, "server.log"));
const delay = ms => new Promise(r => setTimeout(r, ms));
async function until(check, label) {
  for (let i=0;i<100;i++) { if (await check()) return; await delay(100); }
  throw new Error("Timed out: " + label);
}
(async () => {
  let browser;
  const errors = [], sockets = {phone:[],projector:[]}, pages = [];
  try {
    server = spawn(process.env.PYTHON || "python", [path.join(__dirname, "serve_fd_lesson.py"),
      "--bundle", bundle, "--data", profile, "--port", String(port)], {windowsHide:true,stdio:["ignore","pipe","pipe"]});
    server.stdout.pipe(log); server.stderr.pipe(log);
    let startupError;
    server.on("error", error => { startupError = error; });
    await until(() => {
      if (startupError) throw startupError;
      if (server.exitCode !== null) throw new Error("Test server exited before startup; see server.log");
      return fs.existsSync(path.join(profile,"fd-ready.json"));
    }, "owned test server ready");
    base = "http://127.0.0.1:" + JSON.parse(fs.readFileSync(path.join(profile,"fd-ready.json"))).port;
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

    const save = page => page.getByRole("button", {name:"Save answer", exact:true});
    const add = (page, fd) => page.getByRole("button", {name:"Add " + fd, exact:true});
    const attr = (page, name) => page.getByRole("button", {name:"Attribute " + name, exact:true});
    const history = page => page.getByRole("list", {name:"Chosen FD steps"});
    const latest = role => sockets[role].at(-1).plugins.items[0];
    const phoneView = () => Object.values(latest("phone").views)[0].data;
    await add(phone, "f3").waitFor();
    assert(await save(phone).isDisabled());
    await controls.getByRole("button",{name:"Open answers",exact:true}).click();
    await add(phone,"f3").focus(); await phone.keyboard.press("Enter");
    await add(phone,"f4").click();
    for (const name of ["tutor","room","building"]) await attr(phone,name).tap();
    assert.equal(await history(phone).locator("li").count(),2);
    const otherContext = await browser.newContext({storageState:await mobile.storageState(),viewport:{width:390,height:844}});
    const other = await otherContext.newPage(); watch(other);
    await other.goto(base+"/play?pin="+pin);
    await add(other,"f3").waitFor();
    await attr(phone,"room").focus();
    await controls.getByRole("button",{name:"Inspect an answer privately",exact:true}).click();
    assert(await attr(phone,"room").evaluate(node => node === document.activeElement));
    assert.equal(await attr(phone,"room").getAttribute("aria-pressed"),"true");
    for (const fd of ["f3","f4"]) await add(other,fd).click();
    for (const name of ["tutor","room","building"]) await attr(other,name).click();
    await save(other).click();
    await phone.getByRole("button",{name:"Keep my draft",exact:true}).waitFor();
    assert.equal(await history(phone).locator("li").count(),2);
    await phone.getByRole("button",{name:"Keep my draft",exact:true}).click();
    await save(phone).focus(); await phone.keyboard.press("Enter");
    await until(async () => phoneView().own?.version === 2 && phoneView().own?.status === "saved", "saved replacement");
    await until(async () => (await controls.innerText()).includes("0 / 1 / 0 / 0"), "authoritative result");
    assert.equal(await phone.getByText("Your closure and derivation are correct.",{exact:true}).count(),0);
    assert.equal(sockets.phone.at(-1).me.score,0);
    assert.equal(phoneView().own.points,undefined);
    for (const role of ["phone","projector"]) {
      const d = latest(role), v = Object.values(d.views)[0].data;
      assert(!v.worked && !v.demonstration && !v.own?.feedback);
      assert(!JSON.stringify(d).includes('"private":') && !JSON.stringify(d).includes('"evaluations":'));
    }
    await controls.getByRole("button",{name:"Close answers",exact:true}).click();
    await until(() => save(phone).isDisabled(), "closed submissions");
    const select = controls.getByLabel("Inspect an answer privately");
    await select.selectOption({index:1});
    await controls.getByRole("button",{name:"Inspect an answer privately",exact:true}).click();
    await controls.getByText("Your closure and derivation are correct.",{exact:true}).waitFor();
    assert(await controls.getByRole("button",{name:"Share selected answer anonymously",exact:true}).isDisabled());
    await controls.getByRole("button",{name:"Reveal solution",exact:true}).click();
    await phone.getByText("Your closure and derivation are correct.",{exact:true}).waitFor();
    await phone.getByText("Points awarded: 100 / 100",{exact:true}).waitFor();
    await until(() => sockets.phone.at(-1).me.score === 100, "released game score");
    assert.equal(sockets.phone.at(-1).me.rank,1);
    assert(await controls.getByRole("button",{name:"Open answers",exact:true}).isDisabled());
    await phone.getByText("One worked answer",{exact:true}).click();
    assert.equal(await history(phone).locator("li").count(),2);
    assert(!await phone.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), "320px overflow");
    for (const [name,page] of [["phone",phone],["presenter",presenter],["projector",projector]])
      await page.screenshot({path:path.join(output,name+".png"),fullPage:true});
    await controls.getByRole("button",{name:"Share selected answer anonymously",exact:true}).click();
    await projector.getByText("Anonymously shared answer",{exact:true}).waitFor();
    assert(!JSON.stringify(latest("projector")).includes("Test learner"));
    assert(!Object.values(latest("projector").views)[0].data.participants);
    await controls.getByRole("button",{name:"Start walkthrough",exact:true}).click();
    await projector.getByText("Step-by-step derivation",{exact:true}).waitFor();
    await controls.getByRole("button",{name:"Next step",exact:true}).click();
    await controls.getByText("Step 1 / 2",{exact:true}).waitFor();
    await controls.getByRole("button",{name:"Next step",exact:true}).click();
    await controls.getByText("Step 2 / 2",{exact:true}).waitFor();
    await controls.getByRole("button",{name:"Previous step",exact:true}).click();
    await controls.getByText("Step 1 / 2",{exact:true}).waitFor();
    await controls.getByRole("button",{name:"Clear shared answer",exact:true}).click();
    await projector.getByText("One worked answer",{exact:true}).waitFor();
    await add(phone,"f1").click();
    presenter.once("dialog", dialog => dialog.accept());
    await controls.getByRole("button",{name:"Reset activity",exact:true}).click();
    await until(() => sockets.phone.at(-1).me.score === 0, "reset withdraws activity points");
    assert.equal(phoneView().own?.points,undefined);
    await phone.getByRole("button",{name:"Reload saved answer",exact:true}).waitFor();
    await phone.getByRole("button",{name:"Reload saved answer",exact:true}).click();
    assert.equal(await history(phone).locator("li").count(),0);
    assert.equal(await attr(phone,"room").getAttribute("aria-pressed"),"false");
    await presenter.locator("#next").click();
    await phone.getByRole("heading",{name:"Start with a person and a workshop",exact:true}).waitFor();
    await controls.getByRole("button",{name:"Open answers",exact:true}).click();
    await add(phone,"f4").tap();
    await until(() => save(phone).isEnabled(), "practice save enabled");
    await save(phone).tap();
    await phone.getByRole("status").filter({hasText:"This step needs more left-side attributes: {room}"}).waitFor();
    assert(!phoneView().worked);
    await phone.screenshot({path:path.join(output,"practice-feedback.png"),fullPage:true});
    await phone.getByRole("button",{name:"Undo last step",exact:true}).tap();
    for (const fd of ["f1","f3","f4"]) await add(phone,fd).tap();
    for (const name of ["email","tutor","room","building"]) await attr(phone,name).tap();
    await save(phone).tap();
    await phone.getByText("Your closure and derivation are correct.",{exact:true}).waitFor();
    assert(!phoneView().worked);
    assert.equal(phoneView().own.points,undefined);
    assert.equal(sockets.phone.at(-1).me.score,0);
    await presenter.locator("#next").click();
    async function enter(name) {
      await phone.getByRole("heading", {name:source(name).exercise.title.en, exact:true}).waitFor();
      await controls.getByRole("button", {name:"Open answers",exact:true}).click();
      await until(() => save(phone).isEnabled(), "new mode open");
    }
    async function keySet(page, names, attrs) {
      for (const name of attrs) {
        const button = attr(page,name);
        if ((await button.getAttribute("aria-pressed") === "true") !== names.includes(name)) {
          if (page === phone) await button.tap(); else await button.click();
        }
      }
    }
    const status = phrase => phone.getByRole("status").filter({hasText:phrase}).waitFor();
    const keyGood = "Your candidate-key answer is correct.";
    const workshopAttrs = source("keys_one").exercise.attributes.map(a => a.id);
    async function capture(name) {
      assert(!await phone.evaluate(() => document.documentElement.scrollWidth > innerWidth+1), "narrow mode overflow: " + name);
      await phone.screenshot({path:path.join(output,name+"-phone.png"),fullPage:true});
    }
    async function revealMode(name, proof = false) {
      assert(!phoneView().worked && !Object.values(latest("projector").views)[0].data.worked);
      const previousScore = sockets.phone.at(-1).me.score;
      assert.equal(phoneView().own.points,undefined);
      await controls.getByRole("button", {name:"Reveal solution",exact:true}).click();
      await until(() => Boolean(phoneView().worked), "worked answer revealed");
      await phone.getByText("Points awarded: 100 / 100",{exact:true}).waitFor();
      await until(() => sockets.phone.at(-1).me.score === previousScore + 100, "points added once for this mode");
      const roster = controls.getByLabel("Inspect an answer privately"); await roster.selectOption({index:1});
      await controls.getByRole("button", {name:"Inspect an answer privately",exact:true}).click();
      await controls.getByRole("button", {name:"Share selected answer anonymously",exact:true}).click();
      await projector.getByText("Anonymously shared answer", {exact:true}).waitFor();
      const data = Object.values(latest("projector").views)[0].data;
      assert(!data.participants && !data.own && !JSON.stringify(data).includes("alice"));
      assert(!JSON.stringify(latest("projector")).includes('"table":'));
      assert.equal(await controls.getByRole("button", {name:"Start walkthrough",exact:true}).isVisible(), proof);
      if (proof) {
        await controls.getByRole("button",{name:"Start walkthrough",exact:true}).click();
        await controls.getByRole("button",{name:"Next step",exact:true}).click();
        await controls.getByText("Step 1 / 2",{exact:true}).waitFor();
        assert.equal(Object.values(latest("projector").views)[0].data.known,28);
      }
      await presenter.screenshot({path:path.join(output,name+"-presenter.png"),fullPage:true});
      await projector.screenshot({path:path.join(output,name+"-projector.png"),fullPage:true});
      for (const page of [presenter,projector]) {
        const box = page.locator(".fd-overlay");
        await until(() => box.evaluate(node => node.scrollHeight <= node.clientHeight + 1), "complete shared example fits: " + name);
      }
    }
    await enter("keys_one");
    await keySet(phone,["person","email","workshop"],workshopAttrs);
    await phone.getByRole("button",{name:"Use this key",exact:true}).tap();
    await save(phone).tap(); await status("This superkey is not minimal");
    // An unrelated presenter update preserves the in-progress set and focus.
    await keySet(phone,["email","workshop"],workshopAttrs);
    await attr(phone,"email").focus();
    await controls.getByRole("button",{name:"Inspect an answer privately",exact:true}).click();
    assert(await attr(phone,"email").evaluate(node => node === document.activeElement));
    await phone.getByRole("button",{name:"Use this key",exact:true}).tap();
    // The second device saves a competing answer, then the explicit draft wins.
    await keySet(other,["person","workshop"],workshopAttrs);
    await other.getByRole("button",{name:"Use this key",exact:true}).click(); await save(other).click();
    await phone.getByRole("button",{name:"Keep my draft",exact:true}).waitFor();
    await phone.getByRole("button",{name:"Keep my draft",exact:true}).click();
    await save(phone).focus(); await phone.keyboard.press("Enter"); await status(keyGood);
    await capture("keys-one"); await revealMode("keys-one");
    await presenter.locator("#next").click(); await enter("keys_all");
    await keySet(phone,["person","workshop"],workshopAttrs);
    await phone.getByRole("button",{name:"Add key",exact:true}).tap(); await save(phone).tap();
    await status("Candidate keys still missing: 1");
    await keySet(phone,["email","workshop"],workshopAttrs);
    await phone.getByRole("button",{name:"Add key",exact:true}).tap(); await save(phone).tap(); await status(keyGood);
    await capture("keys-all"); await revealMode("keys-all");
    await presenter.locator("#next").click(); await enter("implied");
    await add(phone,"f3").tap(); await save(phone).tap(); await status("The derivation has not reached the target attributes");
    await add(phone,"f4").tap(); await save(phone).tap(); await status("Your derivation proves the target FD.");
    await capture("implied"); await revealMode("implied",true);
    await presenter.locator("#next").click(); await enter("refuted");
    await phone.getByRole("button",{name:"Does not follow",exact:true}).focus(); await phone.keyboard.press("Enter");
    const same = name => phone.getByRole("button",{name:"Same in both rows: " + name,exact:true});
    await same("room").tap(); await save(phone).tap(); await status("The pair violates a given dependency: f4");
    await same("building").tap(); await save(phone).tap(); await status("Your two rows are a valid counterexample.");
    await same("tutor").tap(); await save(phone).tap(); await status("The pair does not violate the target");
    await same("tutor").tap(); await save(phone).tap(); await status("Your two rows are a valid counterexample.");
    await capture("refuted"); await revealMode("refuted");
    await presenter.locator("#next").click(); await enter("different_sizes");
    await keySet(phone,["a"],["a","b","c"]);
    await phone.getByRole("button",{name:"Add key",exact:true}).tap();
    await keySet(phone,["b","c"],["a","b","c"]);
    await phone.getByRole("button",{name:"Add key",exact:true}).tap(); await save(phone).tap(); await status(keyGood);
    await capture("different-sizes"); await revealMode("different-sizes");
    await presenter.locator("#next").click(); await enter("empty_key");
    await save(phone).tap(); await status("Candidate keys still missing: 1");
    await phone.getByRole("button",{name:"Add key",exact:true}).tap();
    await phone.getByRole("button",{name:"Remove key ∅",exact:true}).waitFor();
    await save(phone).tap(); await status(keyGood);
    await capture("empty-key"); await revealMode("empty-key");
    await presenter.locator("#next").click();
    await phone.locator(".participant-input").waitFor({state:"detached"});
    await presenter.locator(".presenter-controls").waitFor({state:"detached"});
    assert.deepEqual(errors,[]);
    const report = {browser:family,version:browser.version(),modes:["closure","keys-one","keys-all","implication-derivation","implication-counterexample","different-size-keys","empty-key"],feedbackPolicies:["after-reveal","practice"],viewport:320,
      grading:"prepared-provider-hook",privacy:true,draftAndFocus:true,keyboard:true,touch:true,sameActorConflict:true,sharing:true,modeSpecificFeedback:true,alternativeKeys:true,alternativeCounterexamples:true,
      walkthrough:true,reset:true,teardown:true,points:true,pointsWithheld:true,pointsReset:true,errors};
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
  if (server?.pid) {
    if (process.platform === "win32") spawnSync("taskkill",["/PID",String(server.pid),"/T","/F"],{windowsHide:true,stdio:"ignore"});
    else server.kill();
  }
  log.end();
});
