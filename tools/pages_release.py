"""Verify an exact final-site archive without rebuilding or publishing.

No catalogue renderer, Core credential, authority issuer or automatic trigger.
Integrity alone is not authority. Runtime transport is deliberately not installed.
"""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
from pathlib import Path, PurePosixPath

VERSION = "chillout.pages-handoff.v1"
MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 100_000


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def receive(archive_path, destination, *, archive_sha256, tree_sha256):
    """Final-site wire check; tree format/budgets are existing #304 inventory v1.

    This never interprets private Delivery evidence or grants publication authority.
    No extractall, links, private envelopes, script execution or post-check rebuild.
    """
    path, destination = Path(archive_path), Path(destination)
    if path.stat().st_size > MAX_BYTES + 64 * 1024 * 1024:
        raise ValueError("archive_budget")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != archive_sha256:
            raise ValueError("archive_digest")
    destination.mkdir(parents=True, exist_ok=False)
    seen, files, total = set(), [], 0
    with tarfile.open(path, "r:") as archive:
        for member in archive:
            name = member.name
            pure = PurePosixPath(name)
            if (
                not member.isfile()
                or name != pure.as_posix()
                or pure.is_absolute()
                or any(p in {".", ".."} or p.endswith(".") for p in pure.parts)
                or re.search(r"[\\:\x00-\x20\x7f]", name)
                or name.casefold() in seen
                or len(seen) >= MAX_FILES
                or name in {"result.json", "input.json", "receipt.json"}
            ):
                raise ValueError("archive_member")
            total += member.size
            if total > MAX_BYTES:
                raise ValueError("site_budget")
            seen.add(name.casefold())
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with archive.extractfile(member) as source, target.open("xb") as output:
                while block := source.read(65536):
                    output.write(block)
                    digest.update(block)
            if target.stat().st_size != member.size:
                raise ValueError("archive_truncated")
            files.append(dict(path=name, bytes=member.size, sha256=digest.hexdigest()))
    # #304 sorts Path components, not the slash-joined string. Preserve that
    # inventory contract on the Linux Pages runner as well as Windows.
    files.sort(key=lambda row: PurePosixPath(row["path"]))
    if "index.html" not in seen or hashlib.sha256(encode(files)).hexdigest() != tree_sha256:
        raise ValueError("site_tree_digest")
    return dict(tree_sha256=tree_sha256, files=len(files), bytes=total)
