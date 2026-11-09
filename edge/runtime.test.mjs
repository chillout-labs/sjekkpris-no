// Synthetic workerd/R2 integration; local only, no account/configuration required.
import {Miniflare} from 'miniflare';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {hash} from './worker.mjs';
const b=x=>new TextEncoder().encode(typeof x==='string'?x:JSON.stringify(x));
const scope='a'.repeat(64),prefix=scope+'/html-v1/',origin='https://fixture.invalid',path='/p/fixture/';
const mf=new Miniflare({modules:true,script:await readFile(new URL('./worker.mjs',import.meta.url),'utf8'),compatibilityDate:'2026-07-30',r2Buckets:['HTML'],bindings:{DELIVERY_SCOPE:scope,PUBLIC_ORIGIN:origin}});
try {
 const bucket=await mf.getR2Bucket('HTML');
 const put=async x=>{const raw=b(x),h=await hash(raw);await bucket.put(prefix+'objects/'+h,raw);return h};
 const now=Math.floor(Date.now()/1000),g=(await hash(b(path))).slice(0,2);
 const html=await put('<html>synthetic active offer</html>'),fallback=await put('<html>synthetic no offers</html>');
 const pages=await put({[path]:{id:'fixture',revision:1,valid_until:now+300,html,fallback}});
 const status=await put({[path]:{id:'fixture',html,min_revision:1,revoked:false,issued_at:now,valid_until:now+300}});
 const root={contract:'chillout.html.v1',scope,sequence:1,pages:{[g]:pages},status:{[g]:status}};
 await bucket.put(prefix+'current',JSON.stringify(root));
 assert.match(await(await mf.dispatchFetch(origin+path)).text(),/active offer/);
 assert.match(await(await mf.dispatchFetch(origin+path)).text(),/active offer/);
 root.status[g]=await put({[path]:{id:'fixture',html,min_revision:1,revoked:true,issued_at:now,valid_until:now+300}});root.sequence++;
 await bucket.put(prefix+'current',JSON.stringify(root));
 assert.match(await(await mf.dispatchFetch(origin+path)).text(),/no offers/);
 // Actual local binding conditional writes: one ETag, two competitors, one winner.
 const before=await bucket.get(prefix+'current');
 const attempts=await Promise.all([3,4].map(n=>bucket.put(prefix+'current',JSON.stringify({...root,sequence:n}),{onlyIf:{etagMatches:before.etag}})));
 assert.equal(attempts.filter(Boolean).length,1);
 assert.equal((await mf.dispatchFetch(origin+'/_test/activate',{method:'POST'})).status,405);
 console.log('PASS: local workerd + private R2 binding, warm cache revocation, conditional race, no write API');
} finally {await mf.dispose()}
