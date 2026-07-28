"""Collect the reviewed platform baseline beside Playwright failure evidence."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=("linux", "win32"), required=True)
    args = parser.parse_args()

    source = WEB / "tests" / "visual" / "__screenshots__" / args.platform
    destination = WEB / "test-results" / "visual-evidence" / "expected"
    if not source.is_dir():
        raise SystemExit(f"reviewed visual baseline is missing: {source}")

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)
    copied = sum(1 for path in destination.rglob("*.png") if path.is_file())
    if copied != 21:
        raise SystemExit(f"expected 21 reviewed baseline images, copied {copied}")
    print(f"Collected {copied} reviewed {args.platform} baseline images.")


if __name__ == "__main__":
    main()
