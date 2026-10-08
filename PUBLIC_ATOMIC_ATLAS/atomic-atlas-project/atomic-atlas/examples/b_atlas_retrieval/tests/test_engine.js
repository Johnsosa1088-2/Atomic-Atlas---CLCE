const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),E=require(path.join(root,'engine.js')),data=JSON.parse(fs.readFileSync(path.join(root,'data.json'),'utf8'));
let passed=0;function test(label,fn){fn();passed++;console.log('PASS '+label)}
test('both retrievers respect the same character cap',()=>{
 for(const q of data.questions)for(const mode of ['atlas','passage']){
  const r=E.retrieve(data,q.text,mode,3800);assert.ok(r.used<=3800);
  assert.equal(r.used,r.selected.reduce((n,c)=>n+E.rendered(c.doc).length+2,0));
 }
});
test('no source identifier is fabricated',()=>{
 const ids=new Set(data.docs.map(d=>d.id));
 for(const mode of ['atlas','passage'])for(const c of E.retrieve(data,'reservoir control law',mode).selected)assert.ok(ids.has(c.doc.id));
});
test('unknown query yields no fake supporting evidence',()=>{
 for(const mode of ['atlas','passage'])assert.equal(E.retrieve(data,'zxqv999999',mode).selected.length,0);
});
test('Atlas includes unresolved response law for reservoir question',()=>{
 const r=E.retrieve(data,data.questions[0].text,'atlas');assert.ok(r.selected.some(c=>c.doc.id==='R-CONTROL'));
 assert.ok(E.prompt(data.questions[0].text,r).includes('unresolved'));
});
test('missing formula is carried as incomplete',()=>{
 const r=E.retrieve(data,'What is the complete P_light formula?','atlas');
 assert.ok(r.selected.some(c=>c.doc.id==='EQ-012'));
 assert.ok(E.prompt('What is the complete P_light formula?',r).includes('right-hand side absent'));
});
test('selected evidence includes source anchor and uncertainty instructions',()=>{
 const r=E.retrieve(data,'reservoirs','atlas');const p=E.prompt('reservoirs',r);
 assert.ok(p.includes('SHA-256:'));assert.ok(p.includes('Do not fill absent terms'));
});
test('same inputs reproduce selected context exactly',()=>{
 assert.deepEqual(E.retrieve(data,'reservoirs','atlas'),E.retrieve(data,'reservoirs','atlas'));
});
console.log(JSON.stringify({tests_passed:passed}));
