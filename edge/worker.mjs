// Read-only Delivery receiver. No upload, activation, price or qualification API.
const HASH = /^[0-9a-f]{64}$/;
const GROUP = /^[0-9a-f]{2}$/;
const PATH = /^\/p\/[a-z0-9]+(?:-[a-z0-9]+)*\/$/;
const VERSION = 'chillout.html.v1';
const MAX_BYTES = 2 * 1024 * 1024;
const MAX_LEASE = 300;
const number = x => Number.isSafeInteger(x) && x >= 0;
const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
export const hash = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
  .map(x => x.toString(16).padStart(2, '0')).join('');
const text = new TextDecoder('utf-8', {fatal: true});
const encode = s => new TextEncoder().encode(s);
const failure = (status, message) => new Response(message, {status, headers: {'Cache-Control': 'no-store'}});

async function bounded(body) {
  const reader = body.getReader(); const parts = []; let size = 0;
  try {
    for (;;) {
      const {value, done} = await reader.read(); if (done) break;
      size += value.byteLength;
      if (size > MAX_BYTES) throw Error('size');
      parts.push(value);
    }
  } finally { await reader.cancel(); }
  const result = new Uint8Array(size); let offset = 0;
  for (const part of parts) { result.set(part, offset); offset += part.byteLength; }
  return result;
}
function validControl(c, scope) {
  return object(c) && c.contract === VERSION && c.scope === scope &&
    number(c.sequence) && object(c.pages) && object(c.status) &&
    [c.pages, c.status].every(shards => Object.keys(shards).length <= 256 &&
      Object.entries(shards).every(([k,v]) => GROUP.test(k) && typeof v === 'string' && HASH.test(v)));
}
function allowed(status, page, now) {
  return object(status) && number(status.issued_at) && number(status.valid_until) &&
    status.issued_at <= now && now < status.valid_until &&
    status.valid_until - status.issued_at <= MAX_LEASE &&
    status.revoked === false && number(status.min_revision) && status.min_revision > 0 &&
    page.revision >= status.min_revision && now < page.valid_until;
}

export async function serve(req, env, {cache, now = () => Math.floor(Date.now()/1000)} = {}) {
  const url = new URL(req.url);
  // Environment is trusted deployment configuration, never derived from Host.
  if (!HASH.test(env.DELIVERY_SCOPE ?? '') || url.origin !== env.PUBLIC_ORIGIN)
    return failure(404, 'Ikke funnet');
  if (!['GET','HEAD'].includes(req.method)) return failure(405, 'Metoden er ikke tillatt');
  if (!PATH.test(url.pathname)) return failure(404, 'Ikke funnet');
  const prefix = env.DELIVERY_SCOPE + '/html-v1/';
  async function control() {
    const o = await env.HTML.get(prefix + 'current');
    if (!o) throw Error('missing');
    const raw = await bounded(o.body), c = JSON.parse(text.decode(raw));
    if (!validControl(c, env.DELIVERY_SCOPE)) throw Error('control');
    return {c, etag: o.etag};
  }
  async function immutable(h) {
    if (typeof h !== 'string' || !HASH.test(h)) throw Error('hash');
    const key = env.PUBLIC_ORIGIN + '/__delivery_cache/' + env.DELIVERY_SCOPE + '/' + h;
    let hit;
    try { hit = await cache?.match(key); } catch {}
    if (hit) {
      const raw = await bounded(hit.body);
      if (await hash(raw) === h) return raw;
    }
    const o = await env.HTML.get(prefix + 'objects/' + h);
    if (!o) throw Error('missing');
    const raw = await bounded(o.body);
    if (await hash(raw) !== h) throw Error('hash');
    // Cache failure is not a failure of the verified origin bytes.
    try { await cache?.put(key, new Response(raw, {headers: {'Cache-Control':'public,max-age=86400'}})); } catch {}
    return raw;
  }
  try {
    const {c, etag} = await control();
    const g = (await hash(encode(url.pathname))).slice(0,2);
    if (!c.pages[g]) return failure(404, 'Ikke funnet');
    const shard = JSON.parse(text.decode(await immutable(c.pages[g])));
    const page = shard[url.pathname];
    if (!page) return failure(404, 'Ikke funnet');
    if (!object(page) || typeof page.id !== 'string' || !page.id ||
        !number(page.revision) || page.revision < 1 || !number(page.valid_until) ||
        !HASH.test(page.html) || !HASH.test(page.fallback)) throw Error('page');
    let status = null;
    try {
      if (c.status[g]) status = JSON.parse(text.decode(await immutable(c.status[g])))[url.pathname];
    } catch {} // Missing/corrupt status must choose the no-offer variant.
    let active = allowed(status, page, now());
    let raw;
    try { raw = await immutable(active ? page.html : page.fallback); }
    catch { active = false; raw = await immutable(page.fallback); }
    // Expiry during I/O and a concurrent revocation cannot bypass the final gate.
    if (active && !allowed(status, page, now())) { active = false; raw = await immutable(page.fallback); }
    const latest = await control();
    if (latest.etag !== etag) return failure(503, 'Produkt midlertidig utilgjengelig');
    if (active && !allowed(status, page, now())) return failure(503, 'Produkt midlertidig utilgjengelig');
    return new Response(req.method === 'HEAD' ? null : raw, {headers: {
      'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
    }});
  } catch { return failure(503, 'Produkt midlertidig utilgjengelig'); }
}
export default { fetch: (req, env) => serve(req, env, {cache: caches.default}) };
