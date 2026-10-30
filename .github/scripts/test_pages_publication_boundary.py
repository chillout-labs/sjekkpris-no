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

    def test_all_event_paths_end_at_read_only_jobs(self):
        jobs = self.active.split('\njobs:\n', 1)[1]
        self.assertEqual(re.findall(r'^  ([\w-]+):$', jobs, re.M),
                         ['test', 'delivery-candidate'])
        self.assertNotRegex(self.active, r'(?m)^\s*(?:pages|id-token|contents|actions):\s*write\b')
        self.assertNotIn('write-all', self.active)
        self.assertNotIn('environment:', self.active)
        self.assertNotIn('needs.test.outputs.operational', self.active)

    def test_no_workflow_has_pages_deploy_capability(self):
        for path in (ROOT / '.github/workflows').glob('*.y*ml'):
            active = '\n'.join(line for line in path.read_text('utf-8').splitlines()
                               if not line.lstrip().startswith('#'))
            with self.subTest(workflow=path.name):
                self.assertNotRegex(active, r'actions/(?:configure-pages|deploy-pages)@')
                self.assertNotRegex(active, r'(?m)^\s*(?:pages|id-token):\s*write\b')

    def test_legacy_api_rebuild_and_secret_are_disconnected(self):
        self.assertNotIn('CHILLOUT_READ_KEY', self.active)
        self.assertNotRegex(self.active, r'python\s+build\.py')
        self.assertNotIn('package_beta.py _site', self.active)
        self.assertNotIn('upload-artifact@', self.active)
        self.assertNotIn('upload-pages-artifact@', self.active)

    def test_dispatch_still_requires_verified_synthetic_candidate(self):
        self.assertIn("if: github.event_name == 'workflow_dispatch' && inputs.delivery_run_id != ''", self.active)
        self.assertIn('--synthetic-only', self.active)
        self.assertIn('--baseline-site', self.active)
        self.assertIn('--result-sha256', self.active)
        self.assertIn('--candidate-tree-sha256 "$CANDIDATE_TREE_SHA256"', self.active)
        self.assertNotRegex(self.active, r'(?m)^      (?:publish|deploy|approve|approved):')


if __name__ == '__main__':
    unittest.main()
