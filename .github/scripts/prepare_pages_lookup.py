"""Adapt one metadata expression in one verified upstream action. No POST changes."""
import hashlib
from pathlib import Path
import sys

UPSTREAM_SHA256 = '63fd34d89cd23d8848618a019f978f2225880a38afe2328e6e7d72f20fc44e89'
ORIGINAL = b'const twirpResponse = await artifactClient.listArtifacts()'
REPLACEMENT = b'''const twirpResponse = await require('./reviewed-artifact-lookup.cjs').lookup(artifactClient, {
        artifactName,
        expectedId: process.env.PAGES_EXPECTED_ARTIFACT_ID,
        expectedRunId: process.env.PAGES_EXPECTED_RUN_ID,
        currentRunId: process.env.GITHUB_RUN_ID,
        log: message => core.info(message)
      })'''


def prepare(action):
    action = Path(action)
    path = action / 'dist/index.js'
    target = path.with_name('reviewed-artifact-lookup.cjs')
    helper = Path(__file__).with_name('reviewed_artifact_lookup.cjs')
    if action.is_symlink() or path.parent.is_symlink() or path.is_symlink() or target.exists():
        raise ValueError('pages_action_path_not_pristine')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != UPSTREAM_SHA256 or raw.count(ORIGINAL) != 1:
        raise ValueError('pages_action_upstream_changed')
    changed = raw.replace(ORIGINAL, REPLACEMENT, 1)
    target.write_bytes(helper.read_bytes())
    path.write_bytes(changed)
    return hashlib.sha256(changed).hexdigest()


if __name__ == '__main__':
    print('Prepared exact pinned Pages metadata lookup:', prepare(sys.argv[1]))
