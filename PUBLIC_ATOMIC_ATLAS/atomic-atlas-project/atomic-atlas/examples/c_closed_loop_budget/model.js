/* Atomic Atlas Example C / 1.0.0 — deterministic dimensionless budget model.
   Project-proposed equations; NOT a Navier–Stokes or engineering steam solver. */
(function(root){
 'use strict';
 const VERSION='ATLAS-C/1.0.0', H=5, TB=1, DT=.1;
 const defaults={heater:.16,cooling:.7,pump:.7,valve:1,steamConnected:true,returnConnected:true};
 function initial(){return {t:0,boiler:1,vapour:0,chamber:0,condensate:0,returnTank:0,U:0,Qin:0,Qout:0,returned:0,flows:{}};}
 function canonical(v){if(v===null||typeof v!=='object')return JSON.stringify(v);if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';}
 function clone(x){return JSON.parse(JSON.stringify(x));}
 function config(c){const p={...defaults,...c};for(const [k,lo,hi] of [['heater',0,.3],['cooling',0,1],['pump',0,1],['valve',0,1]])if(!Number.isFinite(p[k])||p[k]<lo||p[k]>hi)throw Error('Invalid '+k);for(const k of ['steamConnected','returnConnected'])if(typeof p[k]!=='boolean')throw Error('Invalid '+k);return p;}
 function step(old,c,dt=DT){
  const p=config(c);if(!Number.isFinite(dt)||dt<=0||dt>.25)throw Error('Invalid timestep');const s=clone(old);
  const q=s.boiler>.02&&s.vapour<.35-1e-12?p.heater*dt:0;s.U+=q;s.Qin+=q;
  const loss=Math.min(s.U,.012*s.U*dt);s.U-=loss;s.Qout+=loss;
  const e=Math.min(Math.max(0,s.boiler-.02),Math.max(0,.35-s.vapour),.08*dt,Math.max(0,s.U-s.boiler*TB)/(H-TB));
  s.boiler-=e;s.vapour+=e;s.U-=H*e;
  const v=p.steamConnected?Math.min(s.vapour,.12*p.valve*dt):0;s.vapour-=v;s.chamber+=v;
  const d=Math.min(s.chamber,.10*p.cooling*dt);s.chamber-=d;s.condensate+=d;s.Qout+=H*d;
  const r=Math.min(s.condensate,.10*p.pump*dt);s.condensate-=r;s.returnTank+=r;
  const b=p.returnConnected?Math.min(s.returnTank,.10*p.pump*dt):0;s.returnTank-=b;s.boiler+=b;s.returned+=b;
  s.t+=dt;s.flows={evaporation:e/dt,steam:v/dt,condensation:d/dt,pump:r/dt,return:b/dt,heat:q/dt,cooling:(H*d+loss)/dt};
  return s;
 }
 function mass(s){return s.boiler+s.vapour+s.chamber+s.condensate+s.returnTank;}
 function energy(s){return s.U+H*(s.vapour+s.chamber);}
 function balances(s){return {massResidual:mass(s)-1,energyResidual:energy(s)-s.Qin+s.Qout};}
 function phase(s){if(s.flows.return>1e-6)return 'Liquid returning';if(s.flows.condensation>1e-6)return 'Condensing';if(s.flows.steam>1e-6)return 'Vapour transport';if(s.flows.evaporation>1e-6)return 'Evaporating';if(s.U>0)return 'Warming / holding';return 'Cold liquid';}
 function simulate(c,kind='sham',duration=60,cutAt=20){let s=initial(),trace=[];const p=config(c);for(let i=0;i<Math.round(duration/DT);i++){let pc={...p};if(s.t>=cutAt-1e-8){if(kind==='return-cut')pc.returnConnected=false;if(kind==='steam-cut')pc.steamConnected=false;if(kind==='cooling-off')pc.cooling=0;}s=step(s,pc);if(i%10===9)trace.push({t:s.t,returned:s.returned,vapour:s.vapour+s.chamber,...balances(s)});}return {state:s,trace};}
 function compare(c,kind){if(!['sham','return-cut','steam-cut','cooling-off'].includes(kind))throw Error('Unknown intervention');const p={...config(c),steamConnected:true,returnConnected:true};const baseline=simulate(p,'sham'),perturbed=simulate(p,kind);const delta=baseline.state.returned-perturbed.state.returned;return {version:VERSION,evidence:'SIMULATION',protocol:{duration:60,cutAt:20,dt:DT,metric:'cumulative liquid return',intervention:kind,frozenConfig:p},baseline,perturbed,delta,relativeChange:Math.abs(baseline.state.returned)>1e-9?Math.abs(delta)/Math.abs(baseline.state.returned):null,verdict:Math.abs(delta)<1e-9?'No detectable difference in this toy protocol':'Difference detected in this toy protocol'};}
 // Portable SHA-256 for offline file:// operation. Known-answer tests included.
 function sha256(text){
  const bytes=new TextEncoder().encode(text), n=bytes.length, len=Math.ceil((n+9)/64)*64, b=new Uint8Array(len);b.set(bytes);b[n]=128;const dv=new DataView(b.buffer);dv.setUint32(len-8,Math.floor(n/0x20000000));dv.setUint32(len-4,n*8);
  const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  const h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19],rr=(x,n)=>(x>>>n)|(x<<(32-n));
  for(let o=0;o<len;o+=64){const w=new Uint32Array(64);for(let i=0;i<16;i++)w[i]=dv.getUint32(o+i*4);for(let i=16;i<64;i++){const a=w[i-15],z=w[i-2];w[i]=(w[i-16]+(rr(a,7)^rr(a,18)^(a>>>3))+w[i-7]+(rr(z,17)^rr(z,19)^(z>>>10)))>>>0;}
   let [a,b,c,d,e,f,g,z]=h;for(let i=0;i<64;i++){const t1=(z+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+K[i]+w[i])>>>0,t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;z=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;}[a,b,c,d,e,f,g,z].forEach((x,i)=>h[i]=(h[i]+x)>>>0);
  }return h.map(x=>x.toString(16).padStart(8,'0')).join('');
 }
 function append(records,payload){verify(records);const body={schema:'ATLAS-C-RECEIPT/1',sequence:records.length+1,previous:records.length?records.at(-1).hash:null,payload:clone(payload)};return {...body,hash:sha256(canonical(body))};}
 function verify(records){if(!Array.isArray(records))throw Error('Ledger must be an array');let prev=null;for(let i=0;i<records.length;i++){const r=records[i];if(r.schema!=='ATLAS-C-RECEIPT/1'||r.sequence!==i+1||r.previous!==prev)throw Error('Broken order at '+i);const {hash,...body}=r;if(hash!==sha256(canonical(body)))throw Error('Hash mismatch at '+i);prev=hash;}return {count:records.length,head:prev};}
 function replay(records){verify(records);let s=initial(),p=config(defaults);for(const r of records){const q=r.payload;if(q.version!==VERSION)throw Error('Model version mismatch');if(q.kind==='reset'){s=initial();p=config(q.config);}if(!Number.isInteger(q.steps)||q.steps<0||q.steps>100000)throw Error('Invalid step count');for(let i=0;i<q.steps;i++)s=step(s,p);if(q.kind==='config')p=config(q.config);if(canonical(s)!==canonical(q.state)||canonical(p)!==canonical(q.config))throw Error('Replay mismatch at '+r.sequence);}return {state:s,config:p};}
 function recoverAt(records,index,ticks=0){verify(records);if(!Number.isInteger(index)||index<0||index>records.length)throw Error('Invalid receipt index');const limit=records[index]?.payload.steps||0;if(!Number.isInteger(ticks)||ticks<0||ticks>limit)throw Error('Ticks cross next receipt boundary');const q=replay(records.slice(0,index));for(let i=0;i<ticks;i++)q.state=step(q.state,q.config);return q;}
 const api={VERSION,H,TB,DT,defaults,initial,config,step,mass,energy,balances,phase,simulate,compare,canonical,clone,sha256,append,verify,replay,recoverAt};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;root.AtlasC=api;
})(typeof globalThis!=='undefined'?globalThis:this);
