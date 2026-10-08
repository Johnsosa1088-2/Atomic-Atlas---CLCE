// Execute the actual page scripts against a minimal DOM fixture.
// This verifies interactions but is NOT a browser layout/rendering test.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{webcrypto}=require('node:crypto');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const scripts=[...html.matchAll(/<script(?:[^>]*)>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
class Element {
 constructor(tag,id=''){this.tag=tag;this.id=id;this.children=[];this.attrs={};this.value='';this.textContent='';this.dataset={};this.style={};this.listeners={};this.open=false;
  this.classes=new Set();this.classList={toggle:(k,v)=>v?this.classes.add(k):this.classes.delete(k)};}
 append(...children){this.children.push(...children)}
 replaceChildren(...children){this.children=children}
 setAttribute(k,v){this.attrs[k]=String(v)}
 getAttribute(k){return this.attrs[k]}
 addEventListener(k,fn){this.listeners[k]=fn}
 showModal(){this.open=true}
 close(){this.open=false}
 click(){if(this.onclick)this.onclick();if(this.listeners.click)this.listeners.click()}
}
const elements=new Map([...html.matchAll(/<([a-z]+)[^>]*\bid="([^"]+)"[^>]*>/g)].map(x=>[x[2],new Element(x[1],x[2])]));
elements.get('corpus').textContent=scripts[0];
const reviews=['relationships','uncertainty','attribution','constraints'].map(k=>{const s=new Element('select');s.dataset.review=k;return s});
const document={getElementById:id=>{assert.ok(elements.has(id),'Missing DOM element '+id);return elements.get(id)},
 createElement:tag=>new Element(tag),createElementNS:(ns,tag)=>new Element(tag),
 querySelectorAll:q=>q==='[data-review]'?reviews:[]};
const context={document,console,crypto:webcrypto,TextEncoder,Blob,
 URL:{createObjectURL:()=>'',revokeObjectURL:()=>{}},navigator:{clipboard:{writeText:async()=>{}}},
 location:{protocol:'file:',hostname:''},setTimeout,window:{},fetch:()=>{throw Error('Unexpected network use')}};
vm.createContext(context);vm.runInContext(scripts[1],context);vm.runInContext(scripts[2],context);
const get=id=>elements.get(id),tick=()=>new Promise(r=>setTimeout(r,20));
(async()=>{
 assert.ok(get('docs-atlas').children.length);assert.ok(get('prompt').textContent.includes('R-CONTROL'));
 get('mode-passage').click();assert.equal(get('mode-passage').attrs['aria-pressed'],'true');
 get('case').value='formula';get('case').onchange();get('mode-atlas').click();
 assert.ok(get('prompt').textContent.includes('right-hand side absent'));
 get('docs-atlas').children[0].click();assert.equal(get('document').open,true);get('close-doc').click();
 assert.equal(get('document').open,false);
 const group=get('atlas').children.find(c=>c.attrs.role==='button');group.listeners.keydown({key:'Enter',preventDefault(){}});
 assert.ok(get('query').value.includes('Left reservoir'));
 await get('save-trace').onclick();assert.ok(get('history-count').textContent.startsWith('1 event'));
 await get('save-answer').onclick();assert.ok(get('status').textContent.includes('Enter a real answer'));
 get('model').value='DOM test fixture, not a model run';get('answer').value='Fixture output.';
 await get('save-answer').onclick();assert.ok(get('history-count').textContent.startsWith('2 event'));
 get('query').value='zxqv999999';get('query').oninput();get('run').click();assert.ok(get('prompt').textContent.includes('EVIDENCE:\n'));
 assert.equal(get('docs-atlas').children[0].textContent,'No supported evidence selected.');
 get('case').value='reservoir';get('case').onchange();
 // Save actual generated SVG markup for separate diagram inspection.
 const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
 function xml(e){const attrs=Object.entries(e.attrs).map(([k,v])=>' '+k+'="'+escape(v)+'"').join('');
  return '<'+e.tag+attrs+'>'+escape(e.textContent)+e.children.map(xml).join('')+'</'+e.tag+'>'}
 let svg=xml(get('atlas')).replace('<svg','<svg xmlns="http://www.w3.org/2000/svg" width="860" height="650" viewBox="0 0 860 650"');
 const style='<style>text{fill:#eaf1f0;font-family:Arial;font-size:14px}.edge{stroke:#49616a;stroke-width:1.4;fill:none}.edge.on{stroke:#a2dcd2;stroke-width:2.6}.edge-label{font-size:11px;fill:#afc1c9}.node circle{fill:#1b2d39;stroke:#536c77;stroke-width:1.3}.node.on circle{fill:#294d53;stroke:#a2dcd2;stroke-width:2.4}.node.unresolved circle{stroke-dasharray:4 3}</style><rect width="860" height="650" fill="#14212a"/>';
 svg=svg.replace('>', '>'+style);
 fs.writeFileSync(path.join(root,'svg-preview.svg'),svg);
 console.log(JSON.stringify({runtime:'Node VM with minimal DOM fixture',interaction_checks_passed:10,real_browser_layout_tested:false}));
})().catch(e=>{console.error(e);process.exit(1)});
