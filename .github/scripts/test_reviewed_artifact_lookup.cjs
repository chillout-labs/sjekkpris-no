'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {lookup} = require('./reviewed_artifact_lookup.cjs');

function fixture(responses, extra = {}) {
  let time = 0, calls = 0, sleeps = [];
  const options = {artifactName: 'github-pages', expectedId: '42', expectedRunId: '77', currentRunId: '77',
    now: () => time, sleep: async ms => {sleeps.push(ms); time += ms;}, budgetMs: 6000, intervalMs: 2000, ...extra};
  const client = {listArtifacts(...args) {assert.deepEqual(args, []); calls++; const value = responses[Math.min(calls - 1, responses.length - 1)]; if (value instanceof Error) throw value; return value;}};
  return {client, options, calls: () => calls, sleeps, advance: ms => {time += ms;}};
}
const ready = {artifacts: [{id: 42, name: 'github-pages', size: 100}]};
test('empty runtime lists become ready; stop immediately at expected ID', async () => {
  const f = fixture([{artifacts: []}, {artifacts: []}, ready]);
  assert.equal(await lookup(f.client, f.options), ready); assert.equal(f.calls(), 3); assert.deepEqual(f.sleeps, [2000, 2000]);
});
test('permanently empty is bounded by simulated deadline', async () => {
  const f = fixture([{artifacts: []}]); await assert.rejects(lookup(f.client, f.options), /visibility_budget_exhausted/);
  assert.equal(f.calls(), 3); assert.equal(f.sleeps.reduce((a,b) => a+b, 0), 6000);
});
test('ready immediately has no wait or second lookup', async () => {
  const f = fixture([ready]); assert.equal(await lookup(f.client, f.options), ready); assert.equal(f.calls(), 1); assert.deepEqual(f.sleeps, []);
});
for (const [label, artifacts, error] of [
  ['wrong ID', [{id: 43, name: 'github-pages'}], /id_mismatch/],
  ['duplicate name', [{id: 42, name: 'github-pages'}, {id: 43, name: 'github-pages'}], /duplicate/],
  ['expected ID under other name', [{id: 42, name: 'other'}], /name_mismatch/],
  ['duplicate ID', [{id: 42, name: 'github-pages'}, {id: 42, name: 'other'}], /duplicate/],
  ['different run metadata', [{id: 42, name: 'github-pages', workflowRun: {id: 78}}], /run_mismatch/]
]) test(label + ' refuses without retry', async () => {
  const f = fixture([{artifacts}]); await assert.rejects(lookup(f.client, f.options), error); assert.equal(f.calls(), 1); assert.deepEqual(f.sleeps, []);
});
test('different runtime run refuses before first read', async () => {
  const f = fixture([ready], {currentRunId: '78'}); await assert.rejects(lookup(f.client, f.options), /expected_identity_invalid/); assert.equal(f.calls(), 0);
});
test('client failure is not retried or logged as a successful empty list', async () => {
  const error = new Error('synthetic denial'); const f = fixture([error]); await assert.rejects(lookup(f.client, f.options), error); assert.equal(f.calls(), 1);
});
test('malformed metadata refuses without retry', async () => {
  const f = fixture([{}]); await assert.rejects(lookup(f.client, f.options), /metadata_invalid/); assert.equal(f.calls(), 1);
});
test('ready response arriving outside budget is refused', async () => {
  const f = fixture([ready]); f.client.listArtifacts = () => {f.advance(6001); return ready;};
  await assert.rejects(lookup(f.client, f.options), /visibility_budget_exhausted/);
});
test('unrelated artifact never authorizes Pages', async () => {
  const f = fixture([{artifacts: [{id: 15, name: 'test-results'}]}, ready]);
  assert.equal(await lookup(f.client, f.options), ready); assert.equal(f.calls(), 2);
});

test('a hanging metadata read times out without another read', async () => {
  let calls = 0;
  const f = fixture([ready], {schedule: fn => {queueMicrotask(fn); return 1;}, unschedule: () => {}});
  f.client.listArtifacts = () => {calls++; return new Promise(() => {});};
  await assert.rejects(lookup(f.client, f.options), /metadata_timeout/); assert.equal(calls, 1);
});
