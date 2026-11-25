'use strict';

const {performance} = require('node:perf_hooks');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const reference = value => typeof value === 'string' && /^[1-9][0-9]{0,19}$/.test(value);

// Only successful-but-empty current-run metadata is retried. No deployment API.
async function lookup(client, {
  artifactName, expectedId, expectedRunId, currentRunId,
  now = () => performance.now(), sleep = pause, log = () => {},
  budgetMs = 60_000, intervalMs = 2_000, schedule = setTimeout, unschedule = clearTimeout
}) {
  if (!reference(expectedId) || !reference(expectedRunId) || expectedRunId !== currentRunId ||
      artifactName !== 'github-pages' || !Number.isFinite(budgetMs) || budgetMs <= 0 ||
      !Number.isFinite(intervalMs) || intervalMs <= 0) {
    throw new Error('pages_artifact_expected_identity_invalid');
  }
  const deadline = now() + budgetMs;
  const maximum = Math.ceil(budgetMs / intervalMs) + 1;
  for (let attempt = 1; attempt <= maximum; attempt++) {
    const remaining = deadline - now();
    if (remaining <= 0) break;
    let timer;
    let response;
    try {
      // Bound a slow metadata read too; never launch another read after timeout.
      response = await Promise.race([
        client.listArtifacts(), // Same runtime/Twirp client, intentionally no findBy.
        new Promise((_, reject) => {
          timer = schedule(() => reject(new Error('pages_artifact_metadata_timeout')), remaining);
        })
      ]);
    } finally {
      unschedule(timer);
    }
    if (now() >= deadline) break;
    if (!response || !Array.isArray(response.artifacts) ||
        response.artifacts.some(a => !a || typeof a !== 'object')) {
      throw new Error('pages_artifact_metadata_invalid');
    }
    const rows = response.artifacts.filter(a => a.name === artifactName);
    const sameId = response.artifacts.filter(a => String(a.id) === expectedId);
    if (rows.length > 1 || sameId.length > 1) throw new Error('pages_artifact_duplicate');
    if (sameId.length && sameId[0].name !== artifactName) {
      throw new Error('pages_artifact_name_mismatch');
    }
    if (rows.length) {
      const artifact = rows[0];
      if (String(artifact.id) !== expectedId ||
          (typeof artifact.id === 'number' && !Number.isSafeInteger(artifact.id))) {
        throw new Error('pages_artifact_id_mismatch');
      }
      if (artifact.workflowRun && String(artifact.workflowRun.id) !== currentRunId) {
        throw new Error('pages_artifact_run_mismatch');
      }
      log(`Pages artifact metadata ready after ${attempt} lookup(s).`);
      return response;
    }
    log(`Pages artifact metadata empty: lookup ${attempt}; waiting within 60-second budget.`);
    await sleep(Math.min(intervalMs, Math.max(0, deadline - now())));
  }
  throw new Error('pages_artifact_visibility_budget_exhausted');
}
module.exports = {lookup};
