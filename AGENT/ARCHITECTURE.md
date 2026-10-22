# Architecture: Zairenkai-Sdk

> Owned by this repository. Document only what inspected code supports, citing file paths.

## Overview

Contracts only: JSON Schemas (draft 2020-12) and the fixtures that check them. No code from this
repository runs on a device. Decision: `docs/adr/0001-canonical-contracts.md`.

## Components

| Path | Responsibility |
|---|---|
| `contracts/core`, `fas`, `zart`, `tuning` | Schemas written here for producers that define their output in code |
| `contracts/modules`, `local-ai` | Schemas defined here (no single producer) |
| `contracts/mirror/` + `contracts/sources.json` | Byte copies of producer-owned schemas at pinned commits |
| `contracts/index.json` | Fixture → schema map, with origin `captured` or `synthetic` |
| `fixtures/captured/` + `SOURCES.json` | Real program output, with source commit and SHA-256 |
| `fixtures/synthetic/` | Hand-written examples for contracts with no producer |
| `tools/zsdk.py` | `validate`, `check-mirrors`, `mirror`; ToolRegistry and invocation checks |
| `tests/test_contracts.py` | Acceptance of captured output and rejection of mutated documents |

## Data flow

Producer commit → (mirror | captured fixture copied with SHA-256) → `zsdk.py validate` /
`check-mirrors` in CI, which fetches the public producers at the pinned commits without
credentials.

## Trust boundaries

None at run time. CI has `contents: read` only and installs the validator from a hash-locked
`requirements.lock`.

## Generated artifacts

`contracts/mirror/*` (by `zsdk.py mirror`), `requirements.lock` (by
`uv pip compile --generate-hashes requirements.in`). Never edit them by hand.
