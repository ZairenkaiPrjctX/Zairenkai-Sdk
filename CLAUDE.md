# CLAUDE.md: Zairenkai-Sdk

Instructions for Claude Code in `ZairenkaiPrjctX/Zairenkai-Sdk`. Keep this file under 200 lines;
put detail in `AGENT/`.

@AGENTS.md
@AGENT/PROJECT_CONTEXT.md

## Current state (read first)

This repository holds the **cross-repository contracts** as JSON Schemas (draft 2020-12), the
fixtures they are checked against, and `tools/zsdk.py` (Python ≥ 3.11, `jsonschema` from
`requirements.lock`). Decision: `docs/adr/0001-canonical-contracts.md`. Overview: `README.md`.

Non-negotiables in this repo:
- Producers stay canonical. `contracts/mirror/` is a byte copy at the commit in
  `contracts/sources.json`; never edit it by hand (`zsdk.py mirror` rewrites it).
- `fixtures/captured/` is real program output with its source commit and SHA-256
  (`SOURCES.json`); never hand-write or edit it. Hand-written examples go in
  `fixtures/synthetic/` and are marked `synthetic` in `contracts/index.json`.
- Schemas for local-model output are closed (`additionalProperties: false`).
- No ztune (GPL-3.0) code here: only schemas of its JSON output and its captured output as data.

## Commands

| Purpose | Command | Status |
|---|---|---|
| Set up | `python3 -m venv .venv && .venv/bin/pip install --require-hashes -r requirements.lock` | Verified. Evidence: fresh venv, Python 3.13, 2026-10-22 |
| Test | `.venv/bin/python -m unittest discover -s tests -v` | Verified. Evidence: 25 passed, 2026-10-22 |
| Validate fixtures | `.venv/bin/python tools/zsdk.py validate` | Verified. Evidence: 33/33 fixtures valid, 2026-10-22 |
| Mirrors | `.venv/bin/python tools/zsdk.py check-mirrors thermaltools=<dir> afid=<dir>` | Verified. Evidence: all mirrors ok against fresh fetches of the pinned commits, 2026-10-22 |
| Workflow lint | `actionlint .github/workflows/ci.yml` | Verified. Evidence: clean, 2026-10-22 |
| Validate agent foundation | `python3 <path-to-.github>/agent-foundation/scripts/validate_agent_setup.py .` | Configured |

Only list commands that exist in this repository. Never invent one.

## Working rules

- Inspect the relevant code before editing it. Preserve unrelated and uncommitted changes.
- Generated files are edited at their source, then regenerated. Managed foundation files
  (listed in `AGENT/.foundation-manifest.json`) are edited in `ZairenkaiPrjctX/.github`, not here.
- Destructive or outward-facing actions (deleting data, force-push, history rewrites,
  publishing releases, deploying, flashing devices) need explicit human approval each time.
- Do not claim a build, test, or signature succeeded without showing the output.

## Git

- Work on a topic branch; open **draft** pull requests; never merge or approve.
- Commits must be cryptographically signed. If signing fails, stop and report the error.
  Trailer format and verification: `AGENT/policies/git-and-commit-signing.md`.

## Where things are

- `AGENT/README.md`: index of the agent library (prompts, policies, playbooks, templates).
- `.claude/skills/`: run `/repo-audit`, `/implement-feature`, `/bug-fix`, `/test-and-verify`,
  `/security-review`, `/release-readiness`.
- `.claude/rules/`: path-scoped rules, loaded automatically.
