"""Fail if the built site carries anything that must never reach a browser.

Run after `build.py`, before upload. Checks every file under the output
directory for:

- `apk_`, the read key's prefix — and the key itself, when it is in the
  environment;
- the Chillout origin's hostname: the browser never calls Chillout, so a page
  naming it means something leaked from the build into the output;
- `prd_`, the platform's product id, which a property never addresses
  products by;
- `/go/`, because clickout is not live yet and no page may link to it.

Reports the file and which rule matched. Never prints the matched value.
"""

from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path


def forbidden() -> dict[str, str]:
    rules = {"read key prefix": "apk_", "platform product id": "prd_", "clickout path": "/go/"}
    key = os.environ.get("CHILLOUT_READ_KEY", "")
    if key:
        rules["read key"] = key
    origin = os.environ.get("CHILLOUT_ORIGIN", "")
    host = urllib.parse.urlsplit(origin).hostname if origin else None
    if host:
        rules["Chillout origin hostname"] = host
    return rules


def check(out: Path) -> list[str]:
    rules = forbidden()
    problems = []
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        text = path.read_bytes().decode("utf-8", errors="replace").lower()
        for name, needle in rules.items():
            if needle.lower() in text:
                problems.append(f"{path.relative_to(out)}: contains the {name}")
    return problems


def main(argv: list[str]) -> int:
    out = Path(argv[1] if len(argv) > 1 else "_site")
    if not out.is_dir():
        print(f"no output at {out}", file=sys.stderr)
        return 1
    problems = check(out)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(f"output clean: {sum(1 for p in out.rglob('*') if p.is_file())} file(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
