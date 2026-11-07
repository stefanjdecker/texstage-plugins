// SPDX-License-Identifier: Apache-2.0
// 64 synthetic protocol participants, one real phone viewport and presenter.
// Timing gates report failures without discarding the measurements.
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const {randomBytes} = require('node:crypto');
const {spawn, spawnSync} = require('node:child_process');
const playwright = require(process.env.TEXSTAGE_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..'), bundle = path.resolve(process.argv[2]);
const family = process.env.BROWSER || 'chromium';
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
  scope:'Loopback: 64 protocol actors, one additional rendered participant connection for actor 1, one actual presenter evaluator; not physical phones.',
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
    for (let i=0;i<64;i++) {
      const p = new Peer(wsURL); await p.ready();
      p.welcome = await p.send({t:'join',pin:hello.pin,nickname:'Synthetic '+(i+1),join_nonce:randomBytes(16).toString('hex')});
      students.push(p);
    }
    browser = await playwright[family].launch({headless:true,
      ...(process.env.TEXSTAGE_BROWSER_CHANNEL ? {channel:process.env.TEXSTAGE_BROWSER_CHANNEL}: {})});
    report.browser = browser.version(); report.node = process.version;
    const desktop = await browser.newContext({viewport:{width:1440,height:1100}});
    await desktop.addInitScript(() => localStorage.setItem('texquiz:presenter-key','plugin-demo-key'));
    const presenter = await desktop.newPage(); presenter.on('pageerror',e => report.errors.push(e.message));
    await presenter.goto(base+'/stage?bundle='+deck.bundle);
    const mobile = await browser.newContext({viewport:{width:320,height:740},hasTouch:true,isMobile:family!=='firefox'});
    await mobile.addInitScript(saved => localStorage.setItem('texquiz:player',JSON.stringify(saved)),
      {pin:hello.pin,token:students[0].welcome.token,nickname:students[0].welcome.nickname});
    const phone = await mobile.newPage(); phone.on('pageerror',e => report.errors.push(e.message));
    await phone.goto(base+'/play?pin='+hello.pin);
    const modes = (process.env.TEXSTAGE_CLASSROOM_MODES ?? 'practice,keys_all,refuted').split(',').filter(Boolean);
    for (const item of modes) {
      console.log('Starting 64-answer burst: '+item);
      const slide = deck.slides.find(s => s.live?.some(l => l.item === item)); assert(slide);
      await host.send({t:'slide',slide:slide.id});
      await until(() => host.descriptor()?.item === item && students.every(p => p.descriptor()?.item === item),'slide views');
      await host.command('open',{control:host.view().data.control_version});
      await until(() => students.every(p => p.view().data.phase === 'open'),'open views');
      await phone.getByRole('button',{name:'Save answer',exact:true}).waitFor();
      if (item === 'refuted') await phone.getByRole('button',{name:'Does not follow',exact:true}).click();
      const compiled = spawnSync(python,['-c',
        'import json,sys; from texstage_fd_lab.model import compile_lesson; print(json.dumps(compile_lesson(json.load(open(sys.argv[1],encoding="utf-8")))[1]))',
        path.join(root,'examples','functional-dependencies','activities',item+'.json')],{encoding:'utf8',windowsHide:true});
      assert.equal(compiled.status,0,compiled.stderr); const answer = JSON.parse(compiled.stdout);
      const start = performance.now();
      const submissions = students.map(async p => {
        const key = item + ':1'; p.sent.set(key, performance.now());
        const r = await p.command('submit',{phase:p.view().data.phase_version,version:0,answer});
        p.acks.set(key,performance.now()); return r;
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
        for (let i=0;i<24;i++) { await phone.keyboard.press('Enter'); await delay(60); }
        await until(async () => (await phone.evaluate(() => window.__fdInputTimes.length))===24,'24 rendered input samples');
        latency.push(...await phone.evaluate(() => window.__fdInputTimes));
      }
      const receipts = await Promise.all(submissions);
      await until(() => students.every(p => p.feedback.has(item+':1')),'64 checked answers',240000);
      const end = performance.now();
      for (const p of students) {
        assert.equal(p.view().data.own.feedback.correct,true);
        assert(!p.view().data.worked && !p.view().data.participants);
        assert(!JSON.stringify(p.descriptor()).includes('"evaluations":'));
      }
      const events = fs.readFileSync(path.join(profile,'classroom-events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
      const snapshot=spawnSync(python,['-c',
        'import json,sqlite3,sys; from pathlib import Path; from texstage.plugins.manifest import canonical; db=sqlite3.connect(Path(sys.argv[1]).as_uri()+"?mode=ro",uri=True); raw=db.execute("SELECT state FROM items WHERE item=?",(sys.argv[2],)).fetchone()[0]; s=json.loads(raw); print(json.dumps({"state_bytes":len(raw.encode()),"max_actor_slot_bytes":max(len(canonical({a:v})) for a,v in s["answers"].items()),"actors":len(s["answers"]),"pending_jobs":db.execute("SELECT count(*) FROM jobs WHERE status IN (\'queued\',\'leased\')").fetchone()[0]}))',
        path.join(profile,'plugins.sqlite3'),item],{encoding:'utf8',windowsHide:true});
      assert.equal(snapshot.status,0,snapshot.stderr);
      const finalState=JSON.parse(snapshot.stdout); assert.equal(finalState.actors,64); assert.equal(finalState.pending_jobs,0);
      const jobs = receipts.flatMap(r => Object.values(r.jobs));
      const queue = [], evaluation = [];
      for (const id of jobs) {
        const created = events.find(e => e.event==='command' && Object.values(e.receipt.jobs || {}).includes(id));
        const leased = events.find(e => e.event==='lease' && e.jobs.some(j => j.id===id));
        const finished = events.find(e => e.event==='finish' && e.job===id && e.accepted);
        assert(created && leased && finished); queue.push(leased.ms-created.ms); evaluation.push(finished.ms-leased.ms);
      }
      const burst = {item,actors:64,total_ms:end-start,
        ack_ms:stats(students.map(p => p.acks.get(item+':1')-p.sent.get(item+':1'))),
        feedback_ms:stats(students.map(p => p.feedback.get(item+':1')-p.sent.get(item+':1'))),
        queue_ms:stats(queue),leased_to_result_ms:stats(evaluation),input_to_frame_ms:stats(latency),
        max_participant_state_bytes:Math.max(...students.map(p => p.maxBytes)),
        max_host_state_bytes:host.maxBytes,
        max_server_rss_bytes:events.some(e=>e.rss_bytes!==null) ? Math.max(...events.map(e=>e.rss_bytes || 0)) : null,
        max_persisted_state_bytes:Math.max(...events.map(e=>e.state_bytes || 0)),
        final_storage:finalState,
        lease_order_matches_acceptance:JSON.stringify(events.filter(e=>e.event==='lease').flatMap(e=>e.jobs.map(j=>j.id)).filter(id=>jobs.includes(id))) ===
          JSON.stringify(events.filter(e=>e.event==='command').flatMap(e=>Object.values(e.receipt.jobs || {})).filter(id=>jobs.includes(id)))};
      burst.targets = {input:latency.length ? burst.input_to_frame_ms.p95<100 : null,
        feedback_p95:burst.feedback_ms.p95<10000,feedback_worst:burst.feedback_ms.max<30000};
      report.bursts.push(burst); console.log(JSON.stringify(burst));
      await phone.screenshot({path:path.join(output,item+'-phone.png'),fullPage:true});
    }
    if (process.env.TEXSTAGE_CLASSROOM_RECONNECT === '1') {
      console.log('Testing evaluator loss, same-actor resume, replay and reset races');
      await presenter.close();
      const item = 'practice', slide = deck.slides.find(s => s.live?.some(l => l.item === item));
      await host.send({t:'slide',slide:slide.id});
      await until(() => host.descriptor()?.item === item && students[0].descriptor()?.item === item,'reconnect slide');
      const initialEpoch = host.view().epoch;
      await host.command('_reset',{});
      await until(() => host.view().epoch > initialEpoch,'reset view');
      await host.command('open',{control:host.view().data.control_version});
      await until(() => students[0].view().data.phase === 'open','reconnect open');
      const answer = {format:1,mode:'closure',closure:63,steps:[0,2,3]};
      const original = students[0];
      const command = original.envelope('submit',{phase:original.view().data.phase_version,version:0,answer});
      const first = await original.send({t:'plugin.command',command}); assert(first.receipt.accepted);
      await until(() => original.view().data.own?.status === 'pending','no evaluator pending');
      await delay(1500);
      assert.equal(original.view().data.own.status,'pending');
      assert(!original.view().data.own.feedback);
      original.close();
      const resumed = new Peer(wsURL); await resumed.ready();
      const welcome = await resumed.send({t:'resume',token:original.welcome.token});
      assert.equal(welcome.player,original.welcome.player);
      await until(() => resumed.view()?.data.own?.status === 'pending','same actor saved answer');
      assert.equal(resumed.view().data.own.version,1);
      const replay = await resumed.send({t:'plugin.command',command});
      assert.deepEqual(replay.receipt,first.receipt);
      async function evaluatorPeer() {
        const p = new Peer(wsURL); await p.ready();
        await p.send({t:'hello',role:'stage',key:'plugin-demo-key',deck:deck.deck,bundle:deck.bundle});
        return p;
      }
      // A real authenticated socket deliberately goes away while holding a lease.
      // The replacement uses the actual browser evaluator and unchanged CSP.
      const holder = await evaluatorPeer();
      const held = (await holder.send({t:'plugin.work'})).jobs;
      assert.equal(held.length,1);
      await host.command('close',{control:host.view().data.control_version});
      await until(() => resumed.view().data.phase === 'closed','close with pending');
      const replacementStart = performance.now(); holder.close();
      const replacement = await desktop.newPage(); replacement.on('pageerror',e=>report.errors.push(e.message));
      await replacement.goto(base+'/stage?bundle='+deck.bundle);
      await until(() => resumed.view().data.own?.status === 'saved','replacement evaluator completes',15000);
      assert.equal(resumed.view().data.own.feedback.correct,true);
      const replacementMs = performance.now()-replacementStart;
      const late = await evaluatorPeer();
      const staleResult = {id:held[0].id,generation:held[0].generation,epoch:held[0].epoch,outcome:{status:'error'}};
      assert.equal((await late.send({t:'plugin.result',result:staleResult})).accepted,false);
      await replacement.close(); late.close();
      const beforeReset = host.view().epoch;
      await host.command('_reset',{}); await until(()=>host.view().epoch>beforeReset,'second reset');
      await host.command('open',{control:host.view().data.control_version});
      await until(()=>resumed.view().data.phase==='open','second open');
      await resumed.command('submit',{phase:resumed.view().data.phase_version,version:0,answer});
      const finalHolder = await evaluatorPeer();
      const [obsolete] = (await finalHolder.send({t:'plugin.work'})).jobs; assert(obsolete);
      const priorEpoch=host.view().epoch; await host.command('_reset',{});
      await until(()=>resumed.view().epoch>priorEpoch,'reset while leased');
      assert.equal((await finalHolder.send({t:'plugin.result',result:{id:obsolete.id,generation:obsolete.generation,
        epoch:obsolete.epoch,outcome:{status:'error'}}})).accepted,false);
      assert(!resumed.view().data.own);
      const events=fs.readFileSync(path.join(profile,'classroom-events.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
      const generations=events.filter(e=>e.event==='lease').flatMap(e=>e.jobs).filter(j=>j.id===held[0].id).map(j=>j.generation);
      assert.deepEqual(generations,[1,2]);
      report.reconnect={absent_evaluator_pending:true,same_actor_resumed:true,replay_same_receipt:true,
        closed_pending_completed:true,replacement_ms:replacementMs,lease_generations:generations,
        stale_result_rejected:true,reset_late_result_rejected:true};
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
