from pathlib import Path
import json
import tempfile
import unittest
from tools.check_design_links import check


class DesignLinksTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'beta').mkdir()

    def write(self,path,text):
        target=self.root/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text)

    def test_packaged_queries_fragments_and_external_clickouts(self):
        self.write('beta/index.html','<a href="/beta/page/?q=x#part">Page</a><a href="https://example.test/go/never-fetch">External</a>')
        self.write('beta/page/index.html','<h1 id="part">Page</h1><a href="../">Back</a>')
        self.assertEqual(check(self.root,'/beta/'),[])

    def test_missing_fragment_and_duplicate_ids(self):
        self.write('beta/index.html','<p id="same"></p><p id="same"></p><a href="#absent">Broken</a>')
        errors=check(self.root,'/beta/')
        self.assertEqual(len(errors),2)
        self.assertTrue(any('duplicate id' in error for error in errors))
        self.assertTrue(any('missing fragment' in error for error in errors))

    def test_missing_deferred_card_and_image(self):
        self.write('beta/index.html','<h1>Page</h1><script type="application/json">[{"card":"/beta/missing-inline.json"}]</script>')
        self.write('beta/cards.json',json.dumps([{'card':'/beta/missing.json'},{'html':'<img src="/beta/missing.webp">'}]))
        self.assertEqual(len(check(self.root,'/beta/')),3)

    def test_empty_scope_is_not_a_success(self):
        self.assertIn('No HTML',check(self.root,'/beta/')[0])
