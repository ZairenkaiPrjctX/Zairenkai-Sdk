# Project context: Zairenkai-Sdk

> Owned by this repository. Update it whenever verified facts change. Label every statement
> **Verified** (with `Evidence:`), **Unverified**, or **Unknown / Not Configured**.

## Identity

| Field | Value | Status |
|---|---|---|
| Repository | `ZairenkaiPrjctX/Zairenkai-Sdk` | Verified. Evidence: GitHub API |
| Visibility | public | Verified. Evidence: `list_repos`, 2026-10-22 |
| Default branch | `dev` | Verified. Evidence: `git ls-remote`, 2026-10-22 |
| Purpose | Canonical cross-repository contracts: JSON Schemas, captured and synthetic fixtures, validator | Verified. Evidence: `contracts/`, `tools/zsdk.py`, `docs/adr/0001-canonical-contracts.md` |
| Licence | Apache-2.0 (`LICENSE`, `NOTICE`), needed for the mirrored Apache-2.0 schemas; the maintainer has not confirmed it yet | **Unverified** (maintainer decision pending) |

## Contents

| Area | Location | Status |
|---|---|---|
| SDK-defined schemas (Core v1, FAS, zart, tuning, module catalog, Local AI) | `contracts/{core,fas,zart,tuning,modules,local-ai}/` | Verified. Evidence: 25 tests, 33 fixtures valid, 2026-10-22 |
| Mirrors (ThermalTools `3bc71fe`, AFID `d9c4290`) | `contracts/mirror/`, `contracts/sources.json` | Verified. Evidence: `check-mirrors` ok, 2026-10-22 |
| Captured fixtures (App `e1ca387`, Core `dec9d79`) | `fixtures/captured/` | Verified. Evidence: SHA-256 per file in `SOURCES.json` |
| Synthetic Local-AI examples | `fixtures/synthetic/local-ai/` | Synthetic by design; no producer exists |
| CI | `.github/workflows/ci.yml` | actionlint clean. **Unverified** on GitHub |

## Key facts and limitations

- No consumer validates against these schemas yet (App, Core and Intelligence-Engine keep their
  own parsers). Verified. Evidence: no reference to `zairenkaiprjctx.github.io/schemas/sdk` outside
  this repository, 2026-10-22.
- The Local-AI schemas have only synthetic examples. **Unverified** against a real producer.

## Authoritative sources

| Topic | Source |
|---|---|
| Repository facts | this file |
| Architecture | `AGENT/ARCHITECTURE.md` |
| Organization standards | `ZairenkaiPrjctX/.github` → `agent-foundation/standards/` |
| Repository list and relationships | `ZairenkaiPrjctX/.github` → `agent-foundation/inventory/repositories.json` |

## Related repositories

- Producers: Zairenkai-Core, Zairenkai-FAS, Zairenkai-ART, Zairenkai-ThermalTools,
  Zairenkai-Database-Source, Zairenkai-Tuning, Zairenkai-App (catalog). Verified. Evidence: `contracts/sources.json`, `fixtures/captured/SOURCES.json`.
- Intended consumer of the Local-AI contracts: Zairenkai-Intelligence-Engine. **Unverified**: it has no code yet.

## Open questions

- Confirm Apache-2.0 for this repository (maintainer).
- Should consumers validate at run time against these schemas, or only in their tests?
- Publish the schemas at their `$id` URLs (ZairenkaiPrjctX.github.io), or keep `$id` as names only?
