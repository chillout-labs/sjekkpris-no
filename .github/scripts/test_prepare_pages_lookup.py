from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pages_lookup_patch', HERE / 'prepare_pages_lookup.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

class ExactActionPatch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); (self.root / 'dist').mkdir()
        self.raw = b'async function metadata() { ' + patch.ORIGINAL + b'; }\n// deployment POST untouched\n'
        (self.root / 'dist/index.js').write_bytes(self.raw)
        self.previous_hash = patch.UPSTREAM_SHA256
        patch.UPSTREAM_SHA256 = hashlib.sha256(self.raw).hexdigest()
        self.addCleanup(setattr, patch, 'UPSTREAM_SHA256', self.previous_hash)

    def test_exactly_one_expression_changes_and_helper_is_copied(self):
        patch.prepare(self.root)
        self.assertEqual((self.root/'dist/index.js').read_bytes(), self.raw.replace(patch.ORIGINAL, patch.REPLACEMENT, 1))
        self.assertEqual((self.root/'dist/reviewed-artifact-lookup.cjs').read_bytes(), (HERE/'reviewed_artifact_lookup.cjs').read_bytes())

    def test_changed_upstream_is_refused_before_writing(self):
        (self.root/'dist/index.js').write_bytes(self.raw+b'changed')
        with self.assertRaisesRegex(ValueError, 'upstream_changed'): patch.prepare(self.root)
        self.assertFalse((self.root/'dist/reviewed-artifact-lookup.cjs').exists())

    def test_missing_or_duplicate_lookup_is_refused(self):
        for raw in [b'no lookup', self.raw+patch.ORIGINAL]:
            with self.subTest(raw=raw):
                (self.root/'dist/index.js').write_bytes(raw);patch.UPSTREAM_SHA256=hashlib.sha256(raw).hexdigest()
                with self.assertRaisesRegex(ValueError, 'upstream_changed'):patch.prepare(self.root)

    def test_existing_helper_or_second_patch_is_refused(self):
        patch.prepare(self.root)
        with self.assertRaisesRegex(ValueError, 'not_pristine'):patch.prepare(self.root)
