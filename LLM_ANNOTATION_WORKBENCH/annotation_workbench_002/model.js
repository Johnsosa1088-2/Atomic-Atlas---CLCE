(function(root){
'use strict';
const clone=x=>JSON.parse(JSON.stringify(x));
function stable(x){if(Array.isArray(x))return '['+x.map(stable).join(',')+']';if(x&&typeof x==='object')return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')+'}';return JSON.stringify(x)}
async function hash(x){const b=new TextEncoder().encode(typeof x==='string'?x:stable(x));return [...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(v=>v.toString(16).padStart(2,'0')).join('')}
function check(ok,msg){if(!ok)throw Error(msg)}
function valid(s){
 check(s&&s.version===1&&Array.isArray(s.images)&&Array.isArray(s.annotations),'Unsupported project');
 check(s.images.length<=30&&s.annotations.length<=5000,'Project exceeds limits');
 const images=new Map(),annotations=new Map();
 for(const i of s.images){check(typeof i.id==='string'&&/^[a-zA-Z0-9_-]{1,100}$/.test(i.id)&&!images.has(i.id),'Duplicate or invalid image ID');images.set(i.id,i);check(/^[a-f0-9]{64}$/.test(i.sha256),'Invalid image hash');check(Number.isInteger(i.width)&&Number.isInteger(i.height)&&i.width>0&&i.height>0&&i.width<=20000&&i.height<=20000,'Invalid dimensions');check(['front','side-left','side-right','back','unspecified'].includes(i.view),'Invalid view');check(typeof i.name==='string'&&i.name.length<=250,'Invalid filename');check(i.data===null||typeof i.data==='string'&&/^data:image\/(png|jpeg|webp);base64,/.test(i.data),'Only PNG/JPEG/WebP images supported')}
 for(const a of s.annotations){check(typeof a.id==='string'&&/^[a-zA-Z0-9_-]{1,100}$/.test(a.id)&&!annotations.has(a.id),'Duplicate annotation ID');annotations.set(a.id,a);check(images.has(a.image_id),'Missing image');check(['landmark','region','connection'].includes(a.kind),'Invalid kind');check(['human','ai'].includes(a.author)&&['accepted','proposed','rejected'].includes(a.status),'Invalid review metadata');check(a.author!=='ai'||a.method&&a.method!=='manual','AI method required');check(typeof a.label==='string'&&a.label.trim().length>0&&a.label.length<=200,'Invalid label');check(a.part_id===null||typeof a.part_id==='string','Invalid part link');check(a.confidence===null||typeof a.confidence==='number'&&a.confidence>=0&&a.confidence<=1,'Invalid confidence');check(Array.isArray(a.points)&&a.points.length<1000,'Invalid points');check(a.kind==='landmark'?a.points.length===1:a.kind==='region'?a.points.length>=3:a.points.length===0,'Wrong geometry');const i=images.get(a.image_id);for(const p of a.points)check(Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&p[0]>=0&&p[0]<=i.width&&p[1]>=0&&p[1]<=i.height,'Point outside source image');check(a.kind!=='connection'||Array.isArray(a.ends)&&a.ends.length===2&&a.ends[0]!==a.ends[1],'Invalid connection')}
 for(const a of s.annotations)if(a.kind==='connection')for(const id of a.ends){const e=annotations.get(id);check(e&&e.kind==='landmark'&&e.image_id===a.image_id,'Connection requires same-image landmarks')}
 return s;
}
async function verify(project){check(project&&project.format==='AURELIA-ANNOTATIONS-001'&&Array.isArray(project.events)&&project.events.length<=10000,'Invalid checkpoint');let prior=null;let last={version:1,images:[],annotations:[]};for(let n=0;n<project.events.length;n++){const e=project.events[n];check(e.seq===n+1&&e.previous===prior,'Broken event order');valid(e.state);check(e.hash===await hash({seq:e.seq,previous:e.previous,action:e.action,utc:e.utc,state:e.state}),'Event hash mismatch');prior=e.hash;last=e.state}valid(project.state);check(stable(last)===stable(project.state),'State differs from event history');return clone(project)}
class Ledger{
 constructor(){this.project={format:'AURELIA-ANNOTATIONS-001',state:{version:1,images:[],annotations:[]},events:[]}}
 async append(action,state){valid(state);const events=this.project.events;const body={seq:events.length+1,previous:events.length?events.at(-1).hash:null,action,utc:new Date().toISOString(),state:clone(state)};const e={...body,hash:await hash(body)};events.push(e);this.project.state=clone(state);return e}
 async load(p){this.project=await verify(p)}
 async undo(){check(this.project.events.length,'Nothing to undo');const events=this.project.events;const previous=events.length>1?events.at(-2).state:{version:1,images:[],annotations:[]};return this.append('undo: restore prior snapshot',previous)}
}
// Storage envelope deduplicates raster bytes without changing original event hashes.
function pack(project){
 const assets=Object.create(null);
 function state(s){return {...s,images:s.images.map(i=>{if(i.data===null)return {...i};check(!assets[i.sha256]||assets[i.sha256]===i.data,'Conflicting bytes for source hash');assets[i.sha256]=i.data;return {...i,data:{$asset:i.sha256}}})}}
 return {format:'AURELIA-CHECKPOINT-TRANSPORT-002',assets,project:{...project,state:state(project.state),events:project.events.map(e=>({...e,state:state(e.state)}))}};
}
async function unpack(input){
 if(input?.format!=='AURELIA-CHECKPOINT-TRANSPORT-002')return input;
 check(input.assets&&typeof input.assets==='object'&&!Array.isArray(input.assets),'Invalid asset table');
 const keys=Object.keys(input.assets);check(keys.length<=300,'Too many historical assets');
 for(const k of keys){const data=input.assets[k];check(/^[a-f0-9]{64}$/.test(k)&&typeof data==='string'&&/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/]*={0,2}$/.test(data),'Invalid embedded asset');const b=Uint8Array.from(atob(data.split(',')[1]),c=>c.charCodeAt(0));const actual=[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(v=>v.toString(16).padStart(2,'0')).join('');check(actual===k,'Embedded asset hash mismatch')}
 const p=input.project;check(p&&Array.isArray(p.events)&&p.events.length<=10000,'Invalid transport project');
 let total=0;const used=new Set();
 function state(s){check(s&&Array.isArray(s.images)&&s.images.length<=30,'Invalid transport state');return {...s,images:s.images.map(i=>{if(i.data===null)return {...i};check(i.data&&typeof i.data==='object'&&i.data.$asset===i.sha256&&Object.hasOwn(input.assets,i.sha256),'Missing or inconsistent asset reference');used.add(i.sha256);const data=input.assets[i.sha256];total+=data.length;check(total<=512*1024*1024,'Expanded history exceeds 512 MiB; split long sessions');return {...i,data}})}}
 const output={...p,state:state(p.state),events:p.events.map(e=>({...e,state:state(e.state)}))};check(used.size===keys.length,'Unreferenced assets in checkpoint');return output;
}
const api={Ledger,valid,verify,stable,hash,clone,pack,unpack};if(typeof module!=='undefined')module.exports=api;else root.AnnotationModel=api;
})(globalThis);
