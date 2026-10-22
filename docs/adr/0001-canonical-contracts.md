# ADR 0001: Producers stay canonical; the SDK mirrors, defines what has no producer, and validates

Status: proposed (2026-10-22). Needs the maintainer's review.

## Context

Every cross-repository contract already has a working producer (Zairenkai-Docs
`architecture/CONTRACTS_AND_VERSIONING.md`):

- Zairenkai-ThermalTools and Zairenkai-Database-Source publish JSON Schemas (`schemas/`).
- Zairenkai-Core (protocol v1), Zairenkai-FAS (status v1), Zairenkai-ART (`zart`, schema 1) and
  Zairenkai-Tuning (`zairenkai.tuning`, schema 1) define their output in Rust, without a schema.
- Zairenkai-App writes the module catalog; no repository owns its schema.
- The Local-AI contracts (`IntentPlan` and the rest) and entitlements have no producer yet.

Captured outputs of the real binaries exist in App and Core. Rewriting the stable v1 interfaces
around a new central definition would break consumers for no gain.

## Decision

1. **A producer that publishes a schema stays canonical.** The SDK keeps a byte-for-byte mirror
   at a pinned commit (`contracts/sources.json`). `tools/zsdk.py check-mirrors` fails when a
   mirror differs from the producer; CI fetches the public producers at the pinned commits.
2. **For a producer without a schema, the SDK writes one** that describes the producer's output,
   citing the source file it was derived from (Core `protocol.rs`, FAS `docs/INTEGRATION.md`,
   zart `obs.rs`/`inspect.rs`, Tuning `contract.rs`). The producer's code remains the
   definition; the schema is checked against its **captured** output, never against a hand-written
   document presented as real.
3. **Contracts with no producer are defined here**: module catalog, Local-AI types, and later
   entitlements. Their examples live in `fixtures/synthetic/` and say so.
4. Producer-owned objects stay open to new optional fields (consumers ignore unknown fields).
   Objects a **local model** produces (`IntentPlan`, `ToolInvocation`) are closed
   (`additionalProperties: false`): an unexpected field from untrusted output fails instead of
   being ignored.
5. GPL boundary: the tuning schema describes ztune's JSON output; it contains no ztune code, so
   this repository stays Apache-2.0.

## Stack

Python ≥ 3.11 with `jsonschema` 4.26.0 (draft 2020-12), installed from `requirements.lock`
with hashes (`uv pip compile --generate-hashes`). It is already the validator of ThermalTools'
`check-schemas.py` and is in AFID's lock; no runtime code ships to devices from this repository.
Generated client types (Kotlin, Rust) are not part of this decision; if added later they come
from a checked-in generator.

## Consequences

- A producer change that alters a mirrored schema fails SDK CI until the pin and mirror move
  together (`zsdk.py mirror NAME=DIR`).
- Captured fixtures are copied with their source commit and SHA-256
  (`fixtures/captured/SOURCES.json`); re-copy them when the producers re-capture.
- Consumers (App, Core, Intelligence-Engine) can validate against the SDK schemas by `$id`.
