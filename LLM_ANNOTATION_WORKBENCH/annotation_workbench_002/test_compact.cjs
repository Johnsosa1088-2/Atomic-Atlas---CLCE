global.crypto=require('node:crypto').webcrypto;
const assert=require('node:assert/strict'),M=require('./model.js'),cryptoNode=require('node:crypto');
(async()=>{
 const bytes=Buffer.alloc(1024*1024,123),sha=cryptoNode.createHash('sha256').update(bytes).digest('hex');
 const image={id:'source',name:'synthetic-size-fixture.png',sha256:sha,width:100,height:100,view:'unspecified',data:'data:image/png;base64,'+bytes.toString('base64')};
 const l=new M.Ledger();for(let i=0;i<32;i++)await l.append('fixture edit '+i,{version:1,images:[image],annotations:[]});
 const oldBytes=Buffer.byteLength(JSON.stringify(l.project)),packed=M.pack(l.project),newBytes=Buffer.byteLength(JSON.stringify(packed));assert(oldBytes>40*1024*1024);assert(newBytes<2*1024*1024);assert.equal(Object.keys(packed.assets).length,1);console.log('PASS repeated-image regression: '+oldBytes+' bytes → '+newBytes+' bytes');
 const restored=await M.unpack(packed);await M.verify(restored);assert.deepEqual(restored,l.project);assert.equal(restored.events.at(-1).hash,l.project.events.at(-1).hash);console.log('PASS exact history and independent hash-anchor recovery');
 const old=await M.unpack(l.project);await M.verify(old);console.log('PASS legacy checkpoint compatibility');
 const missing=M.clone(packed);delete missing.assets[sha];await assert.rejects(()=>M.unpack(missing));console.log('PASS missing asset rejected');
 const changed=M.clone(packed);changed.assets[sha]='data:image/png;base64,YWJj';await assert.rejects(()=>M.unpack(changed));console.log('PASS tampered asset rejected');
 const historical=M.clone(packed);historical.project.events[0].state.images[0].name='tampered';await assert.rejects(async()=>M.verify(await M.unpack(historical)));console.log('PASS historical edit rejected');
 console.log('6 compact checkpoint tests passed; fixture bytes test storage only, not image decoding');
})().catch(e=>{console.error(e);process.exit(1)});
