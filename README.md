# Zairenkai-Sdk

The cross-repository contracts of the Zairenkai ecosystem as JSON Schemas (draft 2020-12), the
real outputs they are checked against, and the tool that checks them. Decision:
[`docs/adr/0001-canonical-contracts.md`](docs/adr/0001-canonical-contracts.md).

| Area | Schemas | Canonical source | Checked against |
|---|---|---|---|
| Core protocol v1 | `contracts/core/` (envelope, health, capabilities, modules, submit result) | Zairenkai-Core `crates/zcore-domain/src/protocol.rs` | zcored output captured by Zairenkai-App |
| FAS | `contracts/fas/` (status, ctl reply) | Zairenkai-FAS `docs/INTEGRATION.md` | zfasd output captured by Zairenkai-App |
| zart | `contracts/zart/` (observation, inspect, dexopt-status) | Zairenkai-ART `crates/zart/src/{obs,inspect}.rs` | zart output captured by Zairenkai-App |
| zthermal | `contracts/mirror/thermaltools/` (mirror) | Zairenkai-ThermalTools `schemas/` | zthermal output captured by Zairenkai-App |
| AFID | `contracts/mirror/afid/` (mirror) | Zairenkai-Database-Source `schemas/` | AFID's own tests |
| Tuning | `contracts/tuning/document.schema.json` | Zairenkai-Tuning `crates/ztune-core/src/contract.rs` (GPL-3.0 producer; no code here) | ztune output captured by Zairenkai-Core |
| Module catalog | `contracts/modules/catalog.schema.json` | this repository | the catalog Zairenkai-App built from the real module zip |
| Local AI | `contracts/local-ai/` (`IntentPlan`, `ToolInvocation`, `ToolDefinition`, `ToolRegistry`, `ActionPreview`, `UserApproval`, `ExecutionResult`, `AgentAuditEvent`, `ModelManifest`, `DeviceCapabilitySnapshot`) | this repository | synthetic examples only (`fixtures/synthetic/`): no producer exists yet |

`contracts/index.json` maps every fixture to its schema and says whether it is **captured**
(real program output, provenance in `fixtures/captured/SOURCES.json`) or **synthetic**.

## Commands

```sh
python3 -m venv .venv && .venv/bin/pip install --require-hashes -r requirements.lock
.venv/bin/python -m unittest discover -s tests -v       # contract tests
.venv/bin/python tools/zsdk.py validate                 # every fixture against its schema
.venv/bin/python tools/zsdk.py check-mirrors thermaltools=<checkout> afid=<checkout>
```

`zsdk.py mirror NAME=DIR` rewrites a mirror from a producer checkout at the pinned commit; move
the pin in `contracts/sources.json` first.

## Rules

- Never edit a mirror or a captured fixture by hand.
- A schema for model output is closed (`additionalProperties: false`); a producer's schema stays
  open to new optional fields.
- Nothing here runs on a device and nothing here proves device behaviour.

Licence: Apache-2.0 (`LICENSE`, `NOTICE`).
