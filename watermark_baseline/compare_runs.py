"""Verify exact W0 repeatability within the same locked environment."""
import argparse
import json
from pathlib import Path

from .__main__ import digest


def compare(first, second):
    manifests = [
        json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        for folder in (first, second)
    ]
    for folder, manifest in zip((first, second), manifests):
        if manifest["status"] != "complete":
            raise ValueError(f"{folder} did not complete")
        actual = {path.name: digest(path) for path in folder.iterdir()
                  if path.name != "manifest.json"}
        if actual != manifest["files"]:
            raise ValueError(f"{folder} differs from its recorded hashes")
    for manifest in manifests:
        manifest.pop("command")
    changed = sorted(key for key in manifests[0].keys() | manifests[1].keys()
                     if manifests[0].get(key) != manifests[1].get(key))
    changed_files = sorted(name for name in manifests[0]["files"].keys() | manifests[1]["files"].keys()
                           if manifests[0]["files"].get(name) != manifests[1]["files"].get(name))
    return {"first": str(first), "second": str(second), "pass": not changed,
            "files_checked": len(manifests[0]["files"]), "changed_manifest_fields": changed,
            "changed_files": changed_files}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()
    result = compare(args.first, args.second)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["pass"] else 1)
