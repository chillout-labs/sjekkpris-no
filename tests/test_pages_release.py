"""Synthetic exact-byte handoff; no API call, dispatch or publication."""

import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools.pages_release import encode, receive


class PagesReleaseTest(unittest.TestCase):
    def archive(self, path, members):
        files = []
        with tarfile.open(path, "w") as out:
            for name, data, kind in members:
                member = tarfile.TarInfo(name)
                member.type = kind
                member.size = len(data)
                out.addfile(member, io.BytesIO(data))
                files.append(
                    dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                )
        return hashlib.sha256(path.read_bytes()).hexdigest(), hashlib.sha256(
            encode(files)
        ).hexdigest()

    def test_exact_final_tree_without_render(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "site.tar"
            sha, tree = self.archive(archive, [("index.html", b"synthetic page", tarfile.REGTYPE)])
            result = receive(archive, root / "site", archive_sha256=sha, tree_sha256=tree)
            self.assertEqual(result["files"], 1)
            self.assertEqual((root / "site/index.html").read_bytes(), b"synthetic page")
            with self.assertRaises(ValueError):
                receive(archive, root / "bad", archive_sha256="0" * 64, tree_sha256=tree)

    def test_unsafe_archive_or_changed_tree_refuses(self):
        cases = [
            ("../outside", tarfile.REGTYPE),
            ("/absolute", tarfile.REGTYPE),
            ("symlink", tarfile.SYMTYPE),
            ("result.json", tarfile.REGTYPE),
            ("index.html", tarfile.REGTYPE),
        ]
        for name, kind in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                sha, tree = self.archive(root / "site.tar", [(name, b"synthetic", kind)])
                with self.assertRaises(ValueError):
                    receive(
                        root / "site.tar",
                        root / "site",
                        archive_sha256=sha,
                        tree_sha256="0" * 64 if name == "index.html" else tree,
                    )

    def test_existing_inventory_uses_path_component_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Path ordering puts a/index.html before a.html; string ordering does not.
            members = [
                ("a/index.html", b"nested", tarfile.REGTYPE),
                ("a.html", b"sibling", tarfile.REGTYPE),
                ("index.html", b"home", tarfile.REGTYPE),
            ]
            sha, tree = self.archive(root / "site.tar", members)
            result = receive(root / "site.tar", root / "site", archive_sha256=sha, tree_sha256=tree)
            self.assertEqual(result["files"], 3)

    def test_duplicate_member_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sha, tree = self.archive(root / "site.tar", [("index.html", b"x", tarfile.REGTYPE)] * 2)
            with self.assertRaises(ValueError):
                receive(root / "site.tar", root / "site", archive_sha256=sha, tree_sha256=tree)


if __name__ == "__main__":
    unittest.main()
