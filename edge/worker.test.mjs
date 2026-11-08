import {test} from 'node:test';
import assert from 'node:assert/strict';
import {serve, hash} from './worker.mjs';
const bytes = x => new TextEncoder().encode(typeof x==='string'?x:JSON.stringify(x));
const scope = 'a'.repeat(64), origin='https://fixture.invalid', path='/p/fixture-product/';
async function fixture() {
  const data=new Map(); let tick=100, tag=1, reads=0;
  const prefix=scope+'/html-v1/';
  const put=async x=>{const b=bytes(x),h=await hash(b);data.set(prefix+'objects/'+h,b);return h};
  const active=await put('<html>Pris 100 <a href="/go/tgt_FIXTURE">Kjøp</a><script type="application/ld+json">{"@type":"Offer","price":"100"}</script></html>');
  const safe=await put('<html>Ingen tilbud</html>');
  const g=(await hash(bytes(path))).slice(0,2);
  const entry={id:'synthetic-product',revision:2,valid_until:250,html:active,fallback:safe};
  const p=await put({[path]:entry});
  const s=await put({[path]:{min_revision:2,revoked:false,issued_at:100,valid_until:200}});
  let control={contract:'chillout.html.v1',scope,sequence:1,pages:{[g]:p},status:{[g]:s}};
  const bucket={async get(k){reads++;let b=k===prefix+'current'?bytes(control):data.get(k);if(!b)return null;return {etag:String(tag),body:new Response(b).body}}};
  const memory=new Map(); const cache={async match(k){return memory.get(k)?.clone()},async put(k,r){memory.set(k,r.clone())}};
  const env={DELIVERY_SCOPE:scope,PUBLIC_ORIGIN:origin,HTML:bucket};
  const request=(opts={})=>serve(new Request(origin+path,opts),env,{cache,now:()=>tick});
  return {data,put,entry,g,prefix,control,env,cache,memory,request,bucket,
    time(t){tick=t}, bump(){tag++;control.sequence++}, get reads(){return reads}};
}
test('valid HTML and JSON-LD served as the same immutable bytes; HEAD no body',async()=>{
 const f=await fixture(), r=await f.request();assert.equal(r.status,200);assert.match(await r.text(),/"price":"100"/);
 assert.equal(r.headers.get('cache-control'),'no-store');assert.equal(await(await f.request({method:'HEAD'})).text(),'');
});
test('revocation precedes new HTML and survives warm immutable cache',async()=>{
 const f=await fixture();await f.request();
 f.control.status[f.g]=await f.put({[ '/p/fixture-product/' ]:{min_revision:2,revoked:true,issued_at:101,valid_until:200}});f.time(101);f.bump();
 const text=await(await f.request()).text();assert.equal(text,'<html>Ingen tilbud</html>');assert.ok(f.memory.size>0);
});
test('lease expiry, missing status and malformed values choose fallback',async()=>{
 for(const state of ['expired','missing','string','future','too-long']){
  const f=await fixture();
  if(state==='expired')f.time(200);
  if(state==='missing')f.control.status={};
  if(['string','future','too-long'].includes(state))f.control.status[f.g]=await f.put({[path]:{min_revision:2,revoked:state==='string'?'false':false,issued_at:state==='future'?101:100,valid_until:state==='too-long'?401:200}});
  assert.equal(await(await f.request()).text(),'<html>Ingen tilbud</html>',state);
 }
});
test('rollback old HTML cannot bypass a newer minimum revision',async()=>{
 const f=await fixture();f.control.pages[f.g]=await f.put({[path]:{...f.entry,revision:1}});f.bump();
 assert.equal(await(await f.request()).text(),'<html>Ingen tilbud</html>');
});
test('missing active HTML uses safe HTML; missing fallback fails closed',async()=>{
 const f=await fixture();f.data.delete(f.prefix+'objects/'+f.entry.html);
 assert.equal(await(await f.request()).text(),'<html>Ingen tilbud</html>');
 f.memory.clear();f.data.delete(f.prefix+'objects/'+f.entry.fallback);assert.equal((await f.request()).status,503);
});
test('poisoned cache is checked and replaced with verified bytes',async()=>{
 const f=await fixture();await f.cache.put(f.env.PUBLIC_ORIGIN+'/__delivery_cache/'+scope+'/'+f.entry.html,new Response('poison'));
 assert.match(await(await f.request()).text(),/Pris 100/);
});
test('cache write failure does not lose verified response',async()=>{
 const f=await fixture();f.cache.put=async()=>{throw Error('fixture cache failure')};assert.equal((await f.request()).status,200);
});
test('concurrent control mutation fails closed',async()=>{
 const f=await fixture();const get=f.bucket.get;let n=0;f.bucket.get=async k=>{if(k.endsWith('/current')&&++n===2)f.bump();return get(k)};
 assert.equal((await f.request()).status,503);
});
test('scope isolation and no write/test endpoint',async()=>{
 const f=await fixture();assert.equal((await f.request({method:'POST'})).status,405);
 assert.equal((await serve(new Request(origin+'/_test/activate'),f.env)).status,404);
 assert.equal((await serve(new Request('https://other.invalid'+path),f.env)).status,404);
 f.env.DELIVERY_SCOPE='b'.repeat(64);assert.equal((await f.request()).status,503);
});
test('client test clock cannot renew expiry',async()=>{
 const f=await fixture();f.time(201);
 const r=await serve(new Request(origin+path+'?test_now=100'),f.env,{cache:f.cache,now:()=>201});
 assert.equal(await r.text(),'<html>Ingen tilbud</html>');
});
test('expired page despite current status and corrupt status use fallback',async()=>{
 const f=await fixture();f.control.pages[f.g]=await f.put({[path]:{...f.entry,valid_until:100}});
 assert.equal(await(await f.request()).text(),'<html>Ingen tilbud</html>');
 const b=await fixture();b.data.set(b.prefix+'objects/'+b.control.status[b.g],bytes('corrupt'));
 assert.equal(await(await b.request()).text(),'<html>Ingen tilbud</html>');
});
