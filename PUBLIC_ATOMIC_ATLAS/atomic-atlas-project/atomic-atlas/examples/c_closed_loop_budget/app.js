(() => {
'use strict';
const M=AtlasC,$=id=>document.getElementById(id),KEY='neutral-atlas-example-c-v1';
let s=M.initial(),p=M.config(M.defaults),records=[],running=false,pending=0,acc=0,last=0,view=null,blocked=false,persistent=true,savedRaw=null;
const controls=['heater','cooling','pump','valve','steamConnected','returnConnected'];
function storageMessage(msg,error=false){$('storage').textContent=msg;$('storage').classList.toggle('error',error);}
try {savedRaw=localStorage.getItem(KEY);if(savedRaw){records=JSON.parse(savedRaw);const result=M.replay(records);s=result.state;p=result.config;}else localStorage.setItem(KEY,'[]'),savedRaw='[]';}
catch(e){if(savedRaw){blocked=true;storageMessage('Saved history failed verification: '+e.message+'. Original storage was left unchanged.',true);}else{persistent=false;storageMessage('Browser persistence unavailable. Session is volatile; export receipts.',true);}}
function payload(kind,extra={}){return {version:M.VERSION,evidence:'SIMULATION',kind,timestamp:new Date().toISOString(),timezone:'UTC',steps:pending,config:M.clone(p),state:M.clone(s),source:{locator:'model.js',formulaVersion:M.VERSION,basis:'PROJECT_PROPOSED',origin:'Current Example 3 / C discussion; no physical measurements'},...extra};}
function capture(kind,extra={}){
 if(blocked)throw Error('History is locked after an integrity/storage conflict.');
 if(persistent&&localStorage.getItem(KEY)!==savedRaw){blocked=true;running=false;throw Error('Another tab changed the ledger. Reload to recover that history; no overwrite was made.');}
 records.push(M.append(records,payload(kind,extra)));pending=0;
 if(persistent){try{savedRaw=JSON.stringify(records);localStorage.setItem(KEY,savedRaw);}catch(e){persistent=false;storageMessage('Storage failed. Session now volatile; export receipts.',true);}}
 renderLedger();return records.at(-1);
}
function genesis(){if(!records.length)capture('reset');}
function guard(fn){return ()=>{try{if(blocked)throw Error('Saved history is locked; reload after inspecting it.');fn();render();}catch(e){running=false;storageMessage(e.message,true);render();}};}
function advance(n){genesis();view=null;for(let i=0;i<n;i++){s=M.step(s,p);pending++;if(pending>=50)capture('checkpoint');}}
function syncControls(){for(const k of controls){if(typeof p[k]==='boolean')$(k).checked=p[k];else $(k).value=p[k];}}
function render(){
 const q=view?view.state:s,c=view?view.config:p,b=M.balances(q);
 $('time').textContent=q.t.toFixed(1)+' s';$('phase').textContent=M.phase(q);$('mass').textContent=b.massResidual.toExponential(1);$('energy').textContent=b.energyResidual.toExponential(1);
 $('boilerValue').textContent=q.boiler.toFixed(3);$('vapourValue').textContent=q.vapour.toFixed(3);$('chamberValue').textContent=q.chamber.toFixed(3);$('condValue').textContent='Condensate: '+q.condensate.toFixed(3);$('returnValue').textContent=q.returnTank.toFixed(3);
 const bh=170*Math.max(0,Math.min(1,q.boiler)),rh=95*Math.max(0,Math.min(1,q.returnTank));
 $('liquidFill').setAttribute('y',310-bh);$('liquidFill').setAttribute('height',bh);$('returnFill').setAttribute('y',435-rh);$('returnFill').setAttribute('height',rh);$('chamberFill').setAttribute('opacity',Math.min(.9,.08+q.chamber*2));
 $('heaterBlock').setAttribute('opacity',c.heater?'.9':'.15');$('heatLabel').textContent=c.heater.toFixed(3)+' units/s';
 $('steamTube').classList.toggle('route-off',!c.steamConnected);$('returnTube').classList.toggle('route-off',!c.returnConnected);$('cutLabel').textContent=c.returnConnected?'':'RETURN EDGE CUT';
 for(const [id,f] of [['fEvap','evaporation'],['fSteam','steam'],['fCond','condensation'],['fReturn','return']]){const on=(q.flows[f]||0)>1e-8;$(id).style.opacity=on?'1':'.1';$(id).classList.toggle('active',on&&running&&!view);}
 $('valveGlyph').setAttribute('transform','rotate('+(c.valve*90)+' 555 150)');$('pumpGlyph').style.opacity=c.pump?'1':'.2';
 $('play').textContent=running?'Pause':'Start';
 $('viewNote').textContent=view?'REPLAY · receipt '+view.index+' + '+(view.ticks||0)+' reconstructed ticks':'Live state · '+(running?'running':'paused');
 for(const k of controls.slice(0,4))$(k+'Out').textContent=p[k].toFixed(2);
 $('replayOut').textContent=view?'#'+view.index:'live';
}
function renderLedger(){
 $('replay').max=records.length;if(!view)$('replay').value=records.length;
 const box=$('ledger');box.replaceChildren();
 for(const r of records.slice(-35).reverse()){const d=document.createElement('details'),sm=document.createElement('summary'),pre=document.createElement('pre');sm.textContent='#'+r.sequence+' · '+r.payload.kind+' · '+r.payload.state.t.toFixed(1)+' s';pre.textContent=JSON.stringify(r,null,2);d.append(sm,pre);box.append(d);}
 if(!blocked)storageMessage(records.length+' receipts · '+(persistent?'browser-local saved':'volatile session')+' · head '+(records.at(-1)?.hash.slice(0,16)||'empty')+'…',!persistent);
}
function drawComparison(c){
 const all=[...c.baseline.trace,...c.perturbed.trace],top=Math.max(.01,...all.map(x=>x.returned))*1.08;
 $('chartTop').textContent=top.toFixed(2);
 for(const [id,t] of [['baselinePlot',c.baseline.trace],['perturbedPlot',c.perturbed.trace]])$(id).setAttribute('d','M50 200 '+t.map(x=>'L'+(50+x.t/60*530).toFixed(2)+' '+(200-x.returned/top*180).toFixed(2)).join(' '));
 $('result').textContent=c.verdict+'. Baseline '+c.baseline.state.returned.toFixed(4)+'; comparison '+c.perturbed.state.returned.toFixed(4)+'; signed difference '+c.delta.toFixed(4)+'. Demo relative change: '+(c.relativeChange===null?'undefined (zero baseline)':(100*c.relativeChange).toFixed(1)+'%')+'.';
}
$('play').addEventListener('click',guard(()=>{genesis();view=null;running=!running;acc=0;capture(running?'start':'pause');}));
$('step').addEventListener('click',guard(()=>{running=false;advance(10);capture('step');}));
$('reset').addEventListener('click',guard(()=>{genesis();if(pending)capture('checkpoint');running=false;view=null;s=M.initial();p=M.config(M.defaults);pending=0;capture('reset');syncControls();}));
for(const k of controls)$(k).addEventListener('change',guard(()=>{genesis();view=null;if(pending)capture('checkpoint');p={...p,[k]:typeof p[k]==='boolean'?$(k).checked:Number($(k).value)};p=M.config(p);capture('config',{changed:k});}));
$('compare').addEventListener('click',guard(()=>{genesis();const c=M.compare(p,$('intervention').value);capture('comparison',{comparison:c});drawComparison(c);}));
$('verify').addEventListener('click',guard(()=>{if(pending)capture('checkpoint');const q=M.replay(records);if(M.canonical(q.state)!==M.canonical(s)||M.canonical(q.config)!==M.canonical(p))throw Error('Current state mismatch');storageMessage('PASS · '+records.length+' hashes verified; all recorded steps re-simulated. LLM recall untested.');}));
$('replay').addEventListener('input',guard(()=>{running=false;if(pending)capture('checkpoint');const n=Number($('replay').value);view={...M.recoverAt(records,n),index:n,ticks:0};$('ticks').max=records[n]?.payload.steps||0;$('ticks').value=0;}));
$('ticks').addEventListener('input',guard(()=>{if(!view)throw Error('Select a replay checkpoint first.');const n=Number($('ticks').value);view={...M.recoverAt(records,view.index,n),index:view.index,ticks:n};}));
$('live').addEventListener('click',guard(()=>{view=null;$('replay').value=records.length;}));
$('export').addEventListener('click',()=>{try{if(pending&&!blocked)capture('checkpoint');const file={schema:'ATLAS-C-EXPORT/1',version:M.VERSION,modelSha256:M.sha256(MODEL_SOURCE),anchor:M.verify(records),records};const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(file,null,2)],{type:'application/json'}));a.download='atlas-c-receipts-'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}catch(e){storageMessage(e.message,true);}});
$('import').addEventListener('change',async()=>{try{if(records.length||pending||blocked)throw Error('Restore requires an empty ledger. Existing history was not changed.');const f=$('import').files[0];if(!f)return;if(f.size>20*1024*1024)throw Error('Receipt export exceeds 20 MB import limit.');const x=JSON.parse(await f.text());if(x.schema!=='ATLAS-C-EXPORT/1'||x.version!==M.VERSION||x.modelSha256!==M.sha256(MODEL_SOURCE))throw Error('Export/model version or source hash mismatch');const a=M.verify(x.records);if(M.canonical(a)!==M.canonical(x.anchor))throw Error('Export anchor mismatch');const q=M.replay(x.records);if(persistent&&localStorage.getItem(KEY)!==savedRaw)throw Error('Another tab changed the ledger.');records=M.clone(x.records);s=q.state;p=q.config;running=false;view=null;if(persistent){savedRaw=JSON.stringify(records);localStorage.setItem(KEY,savedRaw);}syncControls();renderLedger();render();}catch(e){storageMessage('Restore failed: '+e.message,true);}});
window.addEventListener('visibilitychange',()=>{if(document.hidden&&running){running=false;try{if(pending)capture('pause');}catch(e){storageMessage(e.message,true);}render();}});
window.addEventListener('pagehide',()=>{try{if(pending)capture('checkpoint');}catch(e){}});
function frame(now){if(!last)last=now;const elapsed=Math.min(.25,Math.max(0,(now-last)/1000));last=now;if(running&&!blocked){acc+=elapsed*Number($('speed').value);try{while(acc>=M.DT){advance(1);acc-=M.DT;}}catch(e){running=false;storageMessage(e.message,true);}render();}requestAnimationFrame(frame);}
syncControls();renderLedger();render();requestAnimationFrame(frame);
})();

