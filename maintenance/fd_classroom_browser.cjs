// SPDX-License-Identifier: Apache-2.0
// Configurable synthetic protocol participants, one real phone viewport and presenter.
// Timing gates report failures without discarding the measurements.
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const {randomBytes} = require('node:crypto');
const {spawn, spawnSync} = require('node:child_process');
const playwright = require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE || 'playwright');
const {observeEvaluatorTiming,summarizeEvaluatorTiming} = require('./evaluator_timing.cjs');
const root = path.resolve(__dirname, '..'), bundle = path.resolve(process.argv[2]);
const family = process.env.BROWSER || 'chromium';
const actors = Number(process.env.TEXSTAGE_CLASSROOM_ACTORS || 64);
assert(Number.isInteger(actors) && actors >= 1 && actors <= 1000);
const run = process.env.TEXSTAGE_CLASSROOM_RUN || new Date().toISOString().replace(/[:.]/g, '-');
const output = path.join(root, 'artifacts', 'fd-classroom', run, family);
fs.mkdirSync(output, {recursive:true});
const profile = fs.mkdtempSync(path.join(output, 'profile-'));
const python = process.env.PYTHON || 'python';
const deck = JSON.parse(fs.readFileSync(path.join(bundle, 'deck.json')));
const log = fs.createWriteStream(path.join(output, 'server.log'));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn, label, timeout = 30000) {
  const deadline = performance.now() + timeout;
  while (performance.now() < deadline) { if (await fn()) return; await delay(40); }
  throw new Error('Timed out: ' + label);
}
function stats(values) {
  if (!values.length) return {n:0,min:null,p50:null,p95:null,max:null};
  const sorted = values.toSorted((a,b) => a-b);
  return {n:sorted.length, min:sorted[0], p50:sorted[Math.ceil(sorted.length*.5)-1],
    p95:sorted[Math.ceil(sorted.length*.95)-1], max:sorted.at(-1)};
}
const peers = [];
class Peer {
  constructor(url) {
    this.ws = new WebSocket(url); this.pending = new Map(); this.counter = 0;
    this.maxBytes = 0; this.feedback = new Map(); this.sent = new Map(); this.acks = new Map();
    this.ws.addEventListener('message', ({data}) => {
      const m = JSON.parse(String(data));
      if (m.t === 'state') {
        this.state = m; this.maxBytes = Math.max(this.maxBytes, Buffer.byteLength(String(data)));
        const item = m.plugins?.items?.[0];
        if (item) {
          const v = Object.values(item.views)[0]?.data;
          if (v?.own?.status === 'saved') {
            const key = item.item + ':' + v.own.version;
            if (!this.feedback.has(key)) this.feedback.set(key, performance.now());
          }
        }
      }
      if (this.pending.has(m.re)) {
        const {resolve, reject} = this.pending.get(m.re); this.pending.delete(m.re);
        if (m.t === 'error') reject(new Error(JSON.stringify(m))); else resolve(m);
      }
    });
    peers.push(this);
  }
  async ready() { await until(() => this.ws.readyState === WebSocket.OPEN, 'socket ready'); }
  send(message) {
    const id = 'load-' + ++this.counter;
    return new Promise((resolve,reject) => {
      const timer=setTimeout(()=>{this.pending.delete(id); reject(new Error('Protocol reply timeout: '+message.t));},30000);
      this.pending.set(id,{resolve:m=>{clearTimeout(timer);resolve(m);},reject:e=>{clearTimeout(timer);reject(e);}});
      this.ws.send(JSON.stringify({...message,id}));
    });
  }
  descriptor() { return this.state?.plugins?.items?.[0]; }
  view() { return Object.values(this.descriptor()?.views || {})[0]; }
  envelope(operation, payload) {
    const d = this.descriptor(), v = this.view();
    return {type:d.type,item:d.item,operation,payload,epoch:v.epoch,
      expected_revision:v.revision,request_id:randomBytes(16).toString('hex')};
  }
  async command(operation, payload) {
    const command = this.envelope(operation,payload);
    const result = await this.send({t:'plugin.command',command});
    assert.equal(result.receipt?.accepted,true,JSON.stringify(result));
    return result.receipt;
  }
  close() { this.ws.close(); }
}
const report = {format:1, date:new Date().toISOString(), family,
  hardware:{cpu:os.cpus()[0].model,logical_cpus:os.cpus().length,ram_bytes:os.totalmem(),
    platform:os.platform(),release:os.release(),arch:os.arch()},
  scope:`Loopback: ${actors} protocol actors, one additional rendered participant connection for actor 1, one actual presenter evaluator; not physical phones.`,
  quantiles:'Nearest rank; timings in milliseconds unless the field says bytes.', bursts:[], errors:[]};
let server, browser;
(async () => {
  try {
    server = spawn(python,[path.join(__dirname,'serve_fd_classroom.py'),'--bundle',bundle,'--data',profile,'--port','0'],
      {windowsHide:true,stdio:['ignore','pipe','pipe']});
    server.stdout.pipe(log); server.stderr.pipe(log);
    let startupError; server.on('error',e => startupError=e);
    await until(() => {
      if (startupError) throw startupError;
      if (server.exitCode !== null) throw new Error('Server exited; see server.log');
      return fs.existsSync(path.join(profile,'fd-ready.json'));
    },'owned server');
    const base = 'http://127.0.0.1:' + JSON.parse(fs.readFileSync(path.join(profile,'fd-ready.json'))).port;
    await until(async () => { try { return (await fetch(base+'/api/status')).ok; } catch { return false; } },'HTTP');
    const wsURL = base.replace('http:','ws:') + '/ws';
    const host = new Peer(wsURL); await host.ready();
    const hello = await host.send({t:'hello',role:'host',key:'plugin-demo-key',deck:deck.deck,bundle:deck.bundle});
    const students = [];
    for (let i=0;i<actors;i++) {
      const p = new Peer(wsURL); await p.ready();
      p.welcome = await p.send({t:'join',pin:hello.pin,nickname:'Synthetic '+(i+1),join_nonce:randomBytes(16).toString('hex')});
      students.push(p);
    }
    browser = await playwright[family].launch({headless:true,
      ...(process.env.TEXSTAGE_BROWSER_CHANNEL ? {channel:process.env.TEXSTAGE_BROWSER_CHANNEL}: {})});
    report.browser = browser.version(); report.node = process.version;
    const desktop = await browser.newContext({viewport:{width:1440,height:1100}});
    if (process.env.TEXSTAGE_EVALUATOR_PROFILE === '1') await desktop.addInitScript(observeEvaluatorTiming);
    await desktop.addInitScript(() => localStorage.setItem('texquiz:presenter-key','plugin-demo-key'));
    const presenter = await desktop.newPage(); presenter.on('pageerror',e => report.errors.push(e.message));
    await presenter.goto(base+'/stage?bundle='+deck.bundle);
    report.presenterCores = await presenter.evaluate(()=>navigator.hardwareConcurrency);
    // A new presenter chooses the first slide asynchronously after login. Do not
    // race that navigation with the protocol host's first activity selection.
    await until(() => host.state?.session?.slide === deck.slides[0].id, 'presenter initial slide');
    const mobile = await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=='firefox'});
    await mobile.addInitScript(saved => localStorage.setItem('texquiz:player',JSON.stringify(saved)),
      {pin:hello.pin,token:students[0].welcome.token,nickname:students[0].welcome.nickname});
    const phone = await mobile.newPage(); phone.on('pageerror',e => report.errors.push(e.message));
    await phone.goto(base+'/play?pin='+hello.pin);
    const modes = (process.env.TEXSTAGE_CLASSROOM_MODES ?? 'practice,keys_all,refuted').split(',').filter(Boolean);
    const expectedScores = students.map(() => 0);
    let latestAwards = students.map(() => 0);
    report.points = [];
    for (const item of modes) {
      console.log(`Starting ${actors}-answer burst: ${item}`);
      const slide = deck.slides.find(s => s.live?.some(l => l.item === item)); assert(slide);
      await host.send({t:'slide',slide:slide.id});
      await until(() => host.descriptor()?.item === item && students.every(p => p.descriptor()?.item === item),'slide views');
      await host.command('open',{control:host.view().data.control_version});
      await until(() => students.every(p => p.view().data.phase === 'open'),'open views');
      await phone.getByRole('button',{name:'Save answer',exact:true}).waitFor();
      if (item === 'refuted') await phone.getByRole('button',{name:'Does not follow',exact:true}).click();
      const diverse = process.env.TEXSTAGE_CLASSROOM_DIVERSE === '1';
      const compiled = spawnSync(python,[path.join(__dirname,'fd_classroom_cases.py'),
        path.join(root,'examples','functional-dependencies','activities',item+'.json'),String(actors),diverse?'1':'0'],
        {encoding:'utf8',windowsHide:true});
      assert.equal(compiled.status,0,compiled.stderr); let cases = JSON.parse(compiled.stdout);
      report.answerDiversity ||= {};
      report.answerDiversity[item] = {distinct:new Set(cases.map(c=>JSON.stringify(c.answer))).size,
        correct:cases.filter(c=>c.correct).length,incorrect:cases.filter(c=>!c.correct).length};
      for (const version of (process.env.TEXSTAGE_CLASSROOM_REPLACE === '1' ? [1, 2] : [1])) {
        if (version > 1 && diverse) cases = [...cases.slice(1), cases[0]];
        const answerKey = item + ':' + version;
        const start = performance.now();
        const submissions = students.map(async (p,index) => {
          p.sent.set(answerKey, performance.now());
          const r = await p.command('submit',{phase:p.view().data.phase_version,version:version-1,answer:cases[index].answer});
          p.acks.set(answerKey,performance.now()); return r;
        });
        // Trusted keyboard input through Playwright, measured from the browser's
        // keydown timestamp to the first animation frame after DOM feedback.
        const latency = [];
        const toggle = phone.getByRole('button',{name:item==='refuted' ? 'Same in both rows: person' : 'Attribute person',exact:true});
        if (await toggle.count()) {
          await toggle.focus();
          await phone.evaluate(() => {
            window.__fdInputTimes = [];
            if (window.__fdInputListener) document.removeEventListener('keydown',window.__fdInputListener);
            window.__fdInputListener = e => {
              if (e.key === 'Enter' && e.isTrusted) { const t=e.timeStamp; requestAnimationFrame(() => window.__fdInputTimes.push(performance.now()-t)); }
            };
            document.addEventListener('keydown',window.__fdInputListener);
          });
          let samples = 0;
          do {
            assert(performance.now()-start < 240000, 'burst did not finish while sampling input');
            await phone.keyboard.press('Enter'); samples++; await delay(60);
          } while (samples < 24 || !students.every(p => p.feedback.has(answerKey)));
          await until(async () => (await phone.evaluate(() => window.__fdInputTimes.length))===samples,'rendered input samples');
          latency.push(...await phone.evaluate(() => window.__fdInputTimes));
        }
        const receipts = await Promise.all(submissions);
        await until(() => students.every(p => p.feedback.has(answerKey)),`${actors} checked answers`,240000);
        const end = performance.now();
        for (const [index,p] of students.entries()) {
          assert.equal(p.view().data.own.feedback.correct,cases[index].correct);
          assert(!p.view().data.worked && !p.view().data.participants);
          assert(!JSON.stringify(p.descriptor()).includes('"evaluations":'));
        }
        const events = fs.readFileSync(path.join(profile,'classroom-events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
        const snapshot=spawnSync(python,[path.join(__dirname,'fd_classroom_snapshot.py'),
          path.join(profile,'plugins.sqlite3'),item],{encoding:'utf8',windowsHide:true});
        assert.equal(snapshot.status,0,snapshot.stderr);
        const finalState=JSON.parse(snapshot.stdout); assert.equal(finalState.actors,actors); assert.equal(finalState.pending_jobs,0);
        const jobs = receipts.flatMap(r => Object.values(r.jobs));
        assert.equal(jobs.length,0,'Prepared FD grading creates no browser evaluation jobs');
        const queue = [], evaluation = [];
        for (const id of jobs) {
          const created = events.find(e => e.event==='command' && Object.values(e.receipt.jobs || {}).includes(id));
          const leased = events.find(e => e.event==='lease' && e.jobs.some(j => j.id===id));
          const finished = events.find(e => e.event==='finish' && e.job===id && e.accepted);
          assert(created && leased && finished); queue.push(leased.ms-created.ms); evaluation.push(finished.ms-leased.ms);
        }
        const burst = {item,version,actors,evaluation:'prepared-provider-hook',evaluation_jobs:jobs.length,replaced_answers:version>1 && diverse?actors:0,total_ms:end-start,
          ack_ms:stats(students.map(p => p.acks.get(answerKey)-p.sent.get(answerKey))),
          feedback_ms:stats(students.map(p => p.feedback.get(answerKey)-p.sent.get(answerKey))),
          queue_ms:stats(queue),leased_to_result_ms:stats(evaluation),input_to_frame_ms:stats(latency),
          max_participant_state_bytes:Math.max(...students.map(p => p.maxBytes)),
          max_host_state_bytes:host.maxBytes,
          max_server_rss_bytes:events.some(e=>e.rss_bytes!==null) ? Math.max(...events.map(e=>e.rss_bytes || 0)) : null,
          max_persisted_state_bytes:Math.max(...events.map(e=>e.state_bytes || 0)),
          final_storage:finalState,
          all_answers_checked:true};
        burst.targets = {input:latency.length ? burst.input_to_frame_ms.p95<100 : null,
          feedback_p95:burst.feedback_ms.p95<10000,feedback_worst:burst.feedback_ms.max<30000};
        if (process.env.TEXSTAGE_EVALUATOR_PROFILE === '1' && jobs.length) {
          const timings=await presenter.evaluate(ids=>window.__texstageEvaluationTimings.filter(r=>ids.includes(r.job)),jobs);
          assert.equal(timings.length,jobs.length);
          burst.evaluator_timing=summarizeEvaluatorTiming(timings,stats);
        }
        report.bursts.push(burst); console.log(JSON.stringify(burst));
        await phone.screenshot({path:path.join(output,item+'-v'+version+'-phone.png'),fullPage:true});
      }
      assert(students.every((p,i) => p.state.me.score === expectedScores[i] && p.view().data.own.points === undefined), 'unreleased points remain private');
      const maximum = JSON.parse(fs.readFileSync(path.join(root,'examples/functional-dependencies/activities',item+'.json'))).points || 0;
      const publicationStart = performance.now();
      const publication = host.envelope('reveal',{control:host.view().data.control_version});
      const receipt = await host.send({t:'plugin.command',command:publication});
      assert(receipt.receipt.accepted);
      latestAwards = cases.map(c=>c.correct ? maximum : 0);
      latestAwards.forEach((award,i)=>expectedScores[i]+=award);
      await until(() => students.every((p,i) => p.state.me.score === expectedScores[i] &&
        (!maximum || p.view().data.own.points === latestAwards[i])), 'all participant awards');
      const publicationMs = performance.now() - publicationStart;
      const replay = await host.send({t:'plugin.command',command:publication});
      assert.deepEqual(replay.receipt, receipt.receipt);
      assert(students.every((p,i) => p.state.me.score === expectedScores[i]));
      const scoresById = new Map(students.map((p,i)=>[p.state.me.id,expectedScores[i]]));
      const scoresByNickname = new Map(students.map((p,i)=>[p.welcome.nickname,expectedScores[i]]));
      const awardsByNickname = new Map(students.map((p,i)=>[p.welcome.nickname,latestAwards[i]]));
      assert(host.state.players.every(p => p.score === scoresById.get(p.id)));
      const csvResponse = await fetch(base+'/api/results/'+host.state.session.id+'.csv', {headers:{'x-texquiz-key':'plugin-demo-key'}});
      assert(csvResponse.ok, 'presenter results CSV');
      const csv = await csvResponse.text();
      const rows = csv.replace(/^\uFEFF/, '').trim().split(/\r?\n/).map(line => line.split(','));
      assert.equal(rows.length, actors+1);
      assert(rows.slice(1).every(row => Number(row[2]) === scoresByNickname.get(row[1])), 'CSV totals match every actor');
      if (maximum) {
        const pointsColumn = rows[0].indexOf(`${item} activity points`);
        assert(pointsColumn >= 0);
        assert(rows.slice(1).every(row => Number(row[pointsColumn]) === awardsByNickname.get(row[1])));
      }
      report.points.push({item,maximum,actors,total_range:[Math.min(...expectedScores),Math.max(...expectedScores)],publication_ms:publicationMs,replay:true,withheld:true,csv:true});
      if (actors > 25 && process.env.TEXSTAGE_CLASSROOM_PAGES !== '0') {
        const pages = Math.ceil(actors/25);
        for (let page=1;page<pages;page++) {
          await presenter.getByRole('button',{name:'More answers',exact:true}).click();
          await until(()=>host.view().data.roster_page===page,'presenter answer page');
          await presenter.getByText(`Page ${page+1} / ${pages}`,{exact:true}).waitFor();
        }
        const roster = host.view().data.participants;
        assert.equal(roster.at(-1).number,actors);
        assert(roster.length<=25);
        const select=presenter.getByRole('combobox',{name:'Inspect an answer privately',exact:true});
        await select.selectOption(roster.at(-1).actor);
        await presenter.getByRole('button',{name:'Inspect an answer privately',exact:true}).click();
        await until(()=>host.view().data.selected?.status==='saved','last student answer');
        assert.equal(host.view().data.counts.correct,cases.filter(c=>c.correct).length);
        const lastIndex = students.findIndex(p=>p.state.me.id===roster.at(-1).actor);
        assert.equal(host.view().data.selected.feedback.correct,cases[lastIndex].correct);
        if (cases[lastIndex].correct) await presenter.getByText(item==='practice' ? 'Your closure and derivation are correct.' :
          item==='keys_all' ? 'Your candidate-key answer is correct.' : 'Your two rows are a valid counterexample.',{exact:true}).waitFor();
        await presenter.screenshot({path:path.join(output,item+'-last-page.png'),fullPage:true});
        report.roster = {pages,last_student:actors,last_answer_inspected:true};
      }
    }
    const lastAward = report.points.at(-1);
    if (lastAward?.maximum) {
      await host.command('_reset',{}); latestAwards.forEach((award,i)=>expectedScores[i]-=award);
      await until(() => students.every((p,i) => p.state.me.score === expectedScores[i] && !p.view().data.own), 'reset withdraws all latest activity awards');
      report.pointsReset = {actors,remaining_score_range:[Math.min(...expectedScores),Math.max(...expectedScores)],other_activities_preserved:true};
    }
    if (process.env.TEXSTAGE_CLASSROOM_RECONNECT === '1') {
      console.log('Testing feedback without presenter, same-actor resume, replay and reset');
      await presenter.close();
      const item='practice',slide=deck.slides.find(s=>s.live?.some(l=>l.item===item));
      await host.send({t:'slide',slide:slide.id});
      await until(()=>host.descriptor()?.item===item && students[0].descriptor()?.item===item,'reconnect slide');
      const initialEpoch=host.view().epoch;
      await host.command('_reset',{});await until(()=>host.view().epoch>initialEpoch,'reset view');
      await host.command('open',{control:host.view().data.control_version});
      await until(()=>students[0].view().data.phase==='open','reconnect open');
      const answer={format:1,mode:'closure',closure:63,steps:[0,2,3]};
      const original=students[0];
      const command=original.envelope('submit',{phase:original.view().data.phase_version,version:0,answer});
      const start=performance.now();
      const first=await original.send({t:'plugin.command',command});assert(first.receipt.accepted);
      assert.deepEqual(first.receipt.jobs,{});
      await until(()=>original.view().data.own?.status==='saved','feedback without presenter',10000);
      assert.equal(original.view().data.own.feedback.correct,true);
      const feedbackMs=performance.now()-start;
      original.close();
      const resumed=new Peer(wsURL);await resumed.ready();
      const welcome=await resumed.send({t:'resume',token:original.welcome.token});
      assert.equal(welcome.player,original.welcome.player);
      await until(()=>resumed.view()?.data.own?.status==='saved','same actor checked answer');
      assert.equal(resumed.view().data.own.version,1);
      const replay=await resumed.send({t:'plugin.command',command});
      assert.deepEqual(replay.receipt,first.receipt);
      await host.command('close',{control:host.view().data.control_version});
      await until(()=>resumed.view().data.phase==='closed','closed activity');
      assert.equal(resumed.view().data.own.feedback.correct,true);
      const inspector=new Peer(wsURL);await inspector.ready();
      await inspector.send({t:'hello',role:'stage',key:'plugin-demo-key',deck:deck.deck,bundle:deck.bundle});
      assert.deepEqual((await inspector.send({t:'plugin.work'})).jobs,[]);
      const forged={id:'0'.repeat(32),generation:1,epoch:host.view().epoch,outcome:{status:'error'}};
      assert.equal((await inspector.send({t:'plugin.result',result:forged})).accepted,false);
      const beforeReset=host.view().epoch;
      await host.command('_reset',{});await until(()=>resumed.view().epoch>beforeReset,'second reset');
      assert(!resumed.view().data.own);
      assert.deepEqual((await resumed.send({t:'plugin.command',command})).receipt,first.receipt);
      assert(!resumed.view().data.own,'receipt replay cannot restore an old answer');
      const stale=await resumed.send({t:'plugin.command',command:{...command,request_id:randomBytes(16).toString('hex')}});
      assert.equal(stale.receipt.error,'stale-epoch');
      assert.equal((await inspector.send({t:'plugin.result',result:forged})).accepted,false);
      inspector.close();
      report.reconnect={absent_presenter_feedback:true,feedback_ms:feedbackMs,same_actor_resumed:true,
        replay_same_receipt:true,closed_answer_preserved:true,no_evaluation_jobs:true,
        forged_result_rejected:true,reset_stale_command_rejected:true};
      console.log(JSON.stringify(report.reconnect));
    }
    assert.deepEqual(report.errors,[]);
    report.complete = true;
    report.targets_passed = report.bursts.every(b => Object.values(b.targets).every(v=>v!==false));
    if (!report.targets_passed && process.env.TEXSTAGE_CLASSROOM_ENFORCE !== '0') process.exitCode=2;
  } catch (error) { report.failure = error.stack; process.exitCode = 1; console.error(error); }
  finally {
    for (const p of peers) p.close();
    if (browser) await browser.close();
    if (server?.pid) {
      // Windows' venv launcher has a child interpreter and provider processes.
      // Terminate only the tree created by this harness, not all Python tasks.
      if (process.platform === 'win32') spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});
      else server.kill();
    }
    log.end();
    fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2)+'\n');
    console.log('Report: '+path.join(output,'report.json'));
  }
})();
