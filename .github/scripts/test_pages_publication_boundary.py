"""Regression boundary: repository events may verify but cannot publish Pages.

Inspect the checked-in workflow surface, not a mocked event classifier. A future
publisher must replace this closed boundary through an explicitly reviewed change.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PagesPublicationBoundary(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / '.github/workflows/pages.yml').read_text('utf-8')
        self.active = '\n'.join(line for line in self.workflow.splitlines()
                                if not line.lstrip().startswith('#'))

    def test_only_explicit_owner_job_has_deploy_capability(self):
        jobs = self.active.split('\njobs:\n', 1)[1]
        self.assertEqual(re.findall(r'^  ([\w-]+):$', jobs, re.M),
                         ['test', 'delivery-candidate', 'owner-release-check', 'publish-approved'])
        before, publisher = jobs.split('\n  publish-approved:', 1)
        self.assertNotRegex(before, r'(?m)^\s*(?:pages|id-token|contents|actions):\s*write\b')
        self.assertNotIn('upload-pages-artifact@', before)
        self.assertNotIn('deploy-pages@', before)
        self.assertIn("github.event_name == 'workflow_dispatch'", publisher)
        self.assertIn("github.ref == 'refs/heads/main'", publisher)
        self.assertIn("inputs.owner_release_plan != ''", publisher)
        self.assertIn("inputs.delivery_run_id == ''", publisher)
        self.assertIn('github.run_attempt == 1', publisher)
        self.assertIn('needs: owner-release-check', publisher)
        self.assertIn('environment:\n      name: github-pages', publisher)
        self.assertLess(publisher.index('python -m tools.owner_release'),
                        publisher.index('upload-pages-artifact@'))
        self.assertEqual(publisher.count('contents: write'), 1)
        self.assertIn('OWNER_RELEASE_STAGE: publish', publisher)
        self.assertIn('OWNER_RELEASE_STAGE: preflight', before)
        self.assertNotIn('write-all', self.active)

    def test_other_workflows_have_no_pages_deploy(self):
        for path in (ROOT / '.github/workflows').glob('*.y*ml'):
            if path.name == 'pages.yml':
                continue
            active = '\n'.join(line for line in path.read_text('utf-8').splitlines()
                               if not line.lstrip().startswith('#'))
            self.assertNotRegex(active, r'actions/(?:configure-pages|deploy-pages)@')

    def test_legacy_api_rebuild_and_secret_are_disconnected(self):
        self.assertNotIn('CHILLOUT_READ_KEY', self.active)
        self.assertNotRegex(self.active, r'python\s+build\.py')
        self.assertNotIn('package_beta.py _site', self.active)
        self.assertNotIn('upload-artifact@', self.active)

    def test_dispatch_still_requires_verified_synthetic_candidate(self):
        self.assertIn("if: github.event_name == 'workflow_dispatch' && inputs.delivery_run_id != ''", self.active)
        self.assertIn('--synthetic-only', self.active)
        self.assertIn('--baseline-site', self.active)
        self.assertIn('--result-sha256', self.active)
        self.assertIn('--candidate-tree-sha256 "$CANDIDATE_TREE_SHA256"', self.active)
        self.assertNotRegex(self.active, r'(?m)^      (?:publish|deploy|approve|approved):')


if __name__ == '__main__':
    unittest.main()
