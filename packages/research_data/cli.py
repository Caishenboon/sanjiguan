from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    cache_root, clear_cache, get_manifest, load_manifests, normalize_all,
    sync_dataset, validate_manifest,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="research-data")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    sync = commands.add_parser("sync")
    sync.add_argument("dataset_id")
    commands.add_parser("validate")
    commands.add_parser("normalize")
    commands.add_parser("report")
    commands.add_parser("fixture")
    commands.add_parser("clear-cache")
    args = parser.parse_args(argv)
    if args.command == "list":
        output = [{
            "dataset_id": item["dataset_id"],
            "revision": item["pinned_revision"],
            "license_review_status": item["license_review_status"],
            "connector_enabled": item["connector_enabled"],
        } for item in load_manifests()]
    elif args.command == "sync":
        output = {"files": [str(path.relative_to(cache_root())) for path in sync_dataset(args.dataset_id)]}
    elif args.command == "validate":
        errors = {
            item["dataset_id"]: validate_manifest(item)
            for item in load_manifests()
        }
        output = {"valid": not any(errors.values()), "errors": errors}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if output["valid"] else 1
    elif args.command in {"normalize", "report"}:
        output = normalize_all(write_records=args.command == "normalize")
    elif args.command == "fixture":
        fixture = Path("research-data/fixtures/synthetic-provider-shapes.json")
        output = {"fixture": str(fixture), "synthetic": True, "exists": fixture.exists()}
    else:
        clear_cache()
        output = {"cleared": True}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
