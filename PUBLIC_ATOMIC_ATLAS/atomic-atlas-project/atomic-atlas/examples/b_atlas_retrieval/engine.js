(function(global) {
  'use strict';
  const words=s=>String(s).toLowerCase().match(/[a-z0-9_]+/g)||[];
  const stop=new Set(['the','and','a','an','is','are','of','to','what','how','do','does','in','which','who','it','for','from','with','were']);
  const terms=s=>words(s).filter(t=>!stop.has(t));
  function rank(data,query) {
    const q=terms(query),all=data.docs.map(d=>terms(d.title+' '+d.text));
    const df=new Map();
    for(const ts of all)for(const t of new Set(ts))df.set(t,(df.get(t)||0)+1);
    return data.docs.map((doc,i)=>{
      const ts=all[i];let score=0;
      for(const t of new Set(q)){
        const tf=ts.filter(x=>x===t).length;
        if(tf)score+=(1+Math.log(tf))*Math.log(1+(data.docs.length+1)/((df.get(t)||0)+1));
      }
      return {doc,score:score/Math.sqrt(Math.max(1,ts.length)),reason:'Lexical relevance'};
    }).sort((a,b)=>b.score-a.score||a.doc.id.localeCompare(b.doc.id));
  }
  function rendered(doc){
    return '['+doc.id+'] '+doc.title+'\n'+doc.text+'\nSource: '+doc.source.locator+
      '\nBasis: '+doc.basis+'; access: '+doc.source.access+
      '; source date: '+(doc.source.date||'unknown')+' ('+doc.source.date_basis+')'+
      '\nSHA-256: '+doc.source.sha256+
      (doc.literal?'\nCaptured source text: '+doc.literal:'')+'\n';
  }
  function pack(candidates,budget){
    const selected=[];let used=0;
    for(const c of candidates){
      const size=rendered(c.doc).length+2;
      if(size+used>budget)continue;
      selected.push(c);used+=size;
    }
    return {selected,used,budget};
  }
  function retrieve(data,query,mode,budget=3800,focus=null){
    const ranking=rank(data,query);
    if(mode==='passage')return {...pack(ranking.filter(r=>r.score>0),budget),seeds:[],expanded:[],mode};
    if(mode!=='atlas')throw Error('Unknown retrieval mode');
    const normalized=query.toLowerCase();
    const seeds=data.nodes.filter(n=>n.aliases.some(a=>normalized.includes(a))).map(n=>n.id);
    if(focus&&!seeds.includes(focus))seeds.push(focus);
    // A graph seed can also be inferred from the top lexical hit when aliases miss.
    if(!seeds.length&&ranking[0]?.score>0)seeds.push(...ranking[0].doc.entities);
    const expanded=new Set(seeds);
    for(const edge of data.edges){
      if(seeds.includes(edge.from_id))expanded.add(edge.to_id);
      if(seeds.includes(edge.to_id))expanded.add(edge.from_id);
    }
    const roleBonus={constraint:1,unresolved:1.2,relationship:.7,decision:.7,state:.5,evidence:0};
    const candidates=ranking.map(r=>{
      const direct=r.doc.entities.some(e=>seeds.includes(e));
      const adjacent=r.doc.entities.some(e=>expanded.has(e));
      return {...r,score:r.score+(direct?2:adjacent?.65:0)+(adjacent?(roleBonus[r.doc.role]||0):0),
        reason:direct?'Seed entity + '+r.doc.role:adjacent?'Linked entity + '+r.doc.role:'Lexical relevance'};
    }).filter(r=>r.score>0).sort((a,b)=>b.score-a.score||a.doc.id.localeCompare(b.doc.id));
    return {...pack(candidates,budget),seeds,expanded:[...expanded],mode};
  }
  function prompt(query,result){
    return 'Answer the question using only the evidence below. Distinguish proposed models from measurements. '+
      'Keep unresolved laws and incomplete formulas unresolved. Do not fill absent terms. '+
      'Respect decisions and qualifiers. Cite document IDs in square brackets. If evidence is insufficient, say so.\n\n'+
      'QUESTION: '+query+'\n\nEVIDENCE:\n'+result.selected.map(c=>rendered(c.doc)).join('\n');
  }
  const api={words,rank,rendered,pack,retrieve,prompt};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else global.AtlasEngine=api;
})(typeof window!=='undefined'?window:globalThis);
