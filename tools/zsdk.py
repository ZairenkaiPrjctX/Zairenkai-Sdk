#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ZairenkaiPrjctX contributors
"""Zairenkai contract tooling.

  zsdk.py validate                      validate every fixture listed in contracts/index.json
  zsdk.py check-mirrors NAME=DIR ...    compare each mirrored schema with its producer file at the
                                        pinned commit, read from a git checkout of that producer
  zsdk.py mirror NAME=DIR ...           (re)write the mirrors from those checkouts at the pinned
                                        commits and record their SHA-256 in contracts/sources.json

NAME is a producer key of contracts/sources.json (for example `thermaltools`). Nothing is fetched
from the network: the caller provides the checkouts (CI clones the public repositories).
Exit status: 0 when everything holds, 1 on any mismatch or invalid fixture, 2 on usage errors.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
SOURCES = CONTRACTS / "sources.json"
INDEX = CONTRACTS / "index.json"


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def registry() -> Registry:
    """Every schema under contracts/, addressable by its $id, so $ref across files resolves offline."""
    resources = []
    for p in sorted(CONTRACTS.rglob("*.schema.json")):
        schema = load(p)
        Draft202012Validator.check_schema(schema)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def validator(schema_path: str, reg: Registry) -> Draft202012Validator:
    return Draft202012Validator(load(CONTRACTS / schema_path), registry=reg)


def errors_for(schema_path: str, document: Any, reg: Registry) -> list[str]:
    v = validator(schema_path, reg)
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in v.iter_errors(document)]


def registry_errors(tools: list[dict[str, Any]]) -> list[str]:
    """What JSON Schema cannot say about a ToolRegistry: unique ids, and closed, valid parameter schemas."""
    errs = []
    ids = [t["id"] for t in tools]
    errs += [f"duplicate tool id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for t in tools:
        p = t["parameters"]
        try:
            Draft202012Validator.check_schema(p)
        except Exception as e:  # jsonschema.SchemaError; report and continue
            errs.append(f"{t['id']}: parameters are not a valid schema: {e}")
            continue
        if p.get("type") != "object" or p.get("additionalProperties") is not False:
            errs.append(f"{t['id']}: parameters must be a closed object (additionalProperties: false)")
    return errs


def invocation_errors(plan: dict[str, Any], tools: list[dict[str, Any]]) -> list[str]:
    """Every invocation names a registered tool and its arguments satisfy that tool's parameters."""
    by_id = {t["id"]: t for t in tools}
    errs = []
    for inv in plan["invocations"]:
        tool = by_id.get(inv["tool_id"])
        if tool is None:
            errs.append(f"{inv['invocation_id']}: unknown tool {inv['tool_id']}")
            continue
        for e in Draft202012Validator(tool["parameters"]).iter_errors(inv["arguments"]):
            errs.append(f"{inv['invocation_id']}: {e.message}")
    return errs


def cmd_validate() -> int:
    reg = registry()
    index = load(INDEX)
    failures = 0
    tools = load(ROOT / "fixtures/synthetic/local-ai/tool-registry.json")
    for e in registry_errors(tools):
        failures += 1
        print(f"FAIL tool registry: {e}")
    for entry in index["fixtures"]:
        doc = load(ROOT / entry["fixture"])
        errs = errors_for(entry["schema"], doc, reg)
        if not errs and entry["schema"] == "local-ai/intent-plan.schema.json":
            errs = invocation_errors(doc, tools)
        if errs:
            failures += 1
            print(f"FAIL {entry['fixture']} against {entry['schema']}")
            for e in errs[:10]:
                print(f"     {e}")
        else:
            print(f"ok   {entry['fixture']}")
    print(f"{len(index['fixtures']) - failures}/{len(index['fixtures'])} fixtures valid")
    return 1 if failures else 0


def parse_checkouts(args: list[str]) -> dict[str, Path]:
    out = {}
    for a in args:
        if "=" not in a:
            raise SystemExit(f"usage: expected NAME=DIR, got {a!r}")
        name, d = a.split("=", 1)
        out[name] = Path(d)
    if not out:
        raise SystemExit("usage: give at least one NAME=DIR")
    return out


def producer_file(checkout: Path, commit: str, path: str) -> bytes:
    r = subprocess.run(["git", "-C", str(checkout), "show", f"{commit}:{path}"], capture_output=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"{checkout}: cannot read {path} at {commit}: {r.stderr.decode().strip()}")
    return r.stdout


def cmd_mirrors(args: list[str], write: bool) -> int:
    checkouts = parse_checkouts(args)
    sources = load(SOURCES)
    failures = 0
    for name, checkout in checkouts.items():
        prod = sources["producers"].get(name)
        if prod is None:
            raise SystemExit(f"unknown producer {name!r}; known: {sorted(sources['producers'])}")
        for m in prod["mirrors"]:
            try:
                data = producer_file(checkout, prod["commit"], m["source"])
            except RuntimeError as e:
                print(f"FAIL {e}")
                failures += 1
                continue
            target = CONTRACTS / m["mirror"]
            if write:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                m["sha256"] = sha256(data)
                print(f"wrote {m['mirror']}")
            elif not target.is_file() or target.read_bytes() != data:
                print(f"FAIL {m['mirror']} differs from {prod['repository']}@{prod['commit'][:12]}:{m['source']}")
                failures += 1
            else:
                print(f"ok   {m['mirror']}")
    if write:
        SOURCES.write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "validate":
        return cmd_validate()
    if cmd == "check-mirrors":
        return cmd_mirrors(rest, write=False)
    if cmd == "mirror":
        return cmd_mirrors(rest, write=True)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
