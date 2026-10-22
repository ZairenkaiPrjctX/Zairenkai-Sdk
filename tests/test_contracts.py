# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ZairenkaiPrjctX contributors
"""Contract tests: the schemas accept the real outputs and reject what they must reject."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import zsdk  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

REG = zsdk.registry()


def fixture(path: str):
    return zsdk.load(ROOT / path)


def valid(schema: str, doc) -> bool:
    return not zsdk.errors_for(schema, doc, REG)


class SchemasAndIndex(unittest.TestCase):
    def test_every_schema_is_draft_2020_12_with_a_unique_id(self):
        ids = []
        for p in zsdk.CONTRACTS.rglob("*.schema.json"):
            s = zsdk.load(p)
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", s["$schema"], p)
            Draft202012Validator.check_schema(s)
            ids.append(s["$id"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_indexed_fixture_is_valid(self):
        self.assertEqual(0, zsdk.cmd_validate())

    def test_every_sdk_schema_has_a_fixture(self):
        used = {e["schema"] for e in zsdk.load(zsdk.INDEX)["fixtures"]}
        refs_only = {"core/envelope.schema.json", "zart/observation.schema.json",
                     "local-ai/tool-definition.schema.json", "local-ai/tool-invocation.schema.json"}
        for p in zsdk.CONTRACTS.rglob("*.schema.json"):
            rel = p.relative_to(zsdk.CONTRACTS).as_posix()
            if rel.startswith("mirror/") or rel in refs_only:
                continue
            self.assertIn(rel, used, f"{rel} validates no fixture")

    def test_origin_matches_location(self):
        for e in zsdk.load(zsdk.INDEX)["fixtures"]:
            self.assertIn(e["origin"], ("captured", "synthetic"))
            self.assertTrue(e["fixture"].startswith(f"fixtures/{e['origin']}/"), e)

    def test_captured_fixtures_are_byte_identical_to_their_source(self):
        files = zsdk.load(ROOT / "fixtures/captured/SOURCES.json")["files"]
        self.assertTrue(files)
        for f in files:
            data = (ROOT / "fixtures" / f["fixture"]).read_bytes()
            self.assertEqual(f["sha256"], hashlib.sha256(data).hexdigest(), f["fixture"])
            self.assertRegex(f["commit"], r"^[0-9a-f]{40}$")

    def test_mirrors_match_their_recorded_digest(self):
        for name, prod in zsdk.load(zsdk.SOURCES)["producers"].items():
            self.assertRegex(prod["commit"], r"^[0-9a-f]{40}$", name)
            for m in prod["mirrors"]:
                data = (zsdk.CONTRACTS / m["mirror"]).read_bytes()
                self.assertEqual(m["sha256"], hashlib.sha256(data).hexdigest(), m["mirror"])


class CoreProtocol(unittest.TestCase):
    def test_ok_response_cannot_carry_an_error(self):
        doc = fixture("fixtures/captured/app/core/health.json")
        doc["error"] = {"code": "internal", "message": "x"}
        self.assertFalse(valid("core/health.schema.json", doc))

    def test_error_response(self):
        err = {"v": 1, "id": "x", "ok": False, "error": {"code": "rate_limited", "message": "slow down"}}
        self.assertTrue(valid("core/envelope.schema.json", err))
        err["error"]["code"] = "teapot"
        self.assertFalse(valid("core/envelope.schema.json", err))
        self.assertFalse(valid("core/envelope.schema.json", {"v": 1, "id": "x", "ok": False}))

    def test_protocol_version_and_status_vocabulary(self):
        doc = fixture("fixtures/captured/app/core/health.json")
        doc["v"] = 2
        self.assertFalse(valid("core/health.schema.json", doc))
        caps = fixture("fixtures/captured/app/core/capabilities.json")
        caps["result"][0]["status"] = "available"
        self.assertFalse(valid("core/capabilities.schema.json", caps))

    def test_module_version_is_a_struct_never_a_string(self):
        doc = fixture("fixtures/captured/app/core/modules-installed.json")
        doc["result"][0]["version"] = "0.2.0"
        self.assertFalse(valid("core/modules.schema.json", doc))

    def test_tuning_resources_are_core_capabilities(self):
        caps = fixture("fixtures/captured/app/core/capabilities.json")["result"]
        self.assertTrue({c["id"] for c in caps} >= {"tuning.io_scheduler", "tuning.gpu_governor"})


class Tuning(unittest.TestCase):
    def test_a_write_authorization_needs_tier_d_and_a_profile(self):
        doc = fixture("fixtures/captured/tuning/capabilities-synthetic-profile.json")
        authorized = [c for c in doc["capabilities"] if c.get("authorization", {}).get("write_authorized")]
        self.assertTrue(authorized)
        bad = copy.deepcopy(doc)
        for c in bad["capabilities"]:
            if c.get("authorization", {}).get("write_authorized"):
                c["authorization"]["tier"] = "S"
        self.assertFalse(valid("tuning/document.schema.json", bad))
        bad = copy.deepcopy(doc)
        for c in bad["capabilities"]:
            if c.get("authorization", {}).get("write_authorized"):
                del c["authorization"]["profile_id"]
        self.assertFalse(valid("tuning/document.schema.json", bad))

    def test_the_shipped_capabilities_authorize_nothing(self):
        doc = fixture("fixtures/captured/tuning/capabilities.json")
        self.assertFalse(any(c.get("authorization", {}).get("write_authorized") for c in doc["capabilities"]))

    def test_a_failed_reading_never_carries_a_number(self):
        doc = fixture("fixtures/captured/tuning/telemetry.json")
        self.assertEqual("unavailable", doc["cpu"]["load"]["status"])
        self.assertTrue(valid("tuning/document.schema.json", doc))
        doc["cpu"]["load"]["value"] = 0
        self.assertFalse(valid("tuning/document.schema.json", doc))
        doc = fixture("fixtures/captured/tuning/telemetry.json")
        doc["cpu"]["cores"][0]["cur_freq"]["unit"] = "MHz"
        self.assertFalse(valid("tuning/document.schema.json", doc))

    def test_request_and_operation_status_are_separate(self):
        doc = fixture("fixtures/captured/tuning/apply-not-authorized.json")
        self.assertEqual(("rejected", "not_started", "not_authorized"),
                         (doc["request"]["status"], doc["operation"]["status"], doc["error"]["code"]))
        doc["operation"]["status"] = "rejected"
        self.assertFalse(valid("tuning/document.schema.json", doc))


class Catalog(unittest.TestCase):
    def test_entries_cannot_escape_the_module(self):
        doc = fixture("fixtures/captured/app/system-modules/catalog.json")
        doc["modules"][0]["entries"]["../../system/bin/sh"] = "0" * 64
        self.assertFalse(valid("modules/catalog.schema.json", doc))

    def test_ztune_ships_with_its_source(self):
        entries = fixture("fixtures/captured/app/system-modules/catalog.json")["modules"][0]["entries"]
        self.assertIn("bin/ztune", entries)
        self.assertTrue(any(e.startswith("source/zairenkai-tuning/") for e in entries))


class LocalAi(unittest.TestCase):
    PLAN = "fixtures/synthetic/local-ai/intent-plan.json"
    TOOLS = "fixtures/synthetic/local-ai/tool-registry.json"

    def test_model_output_is_closed(self):
        plan = fixture(self.PLAN)
        plan["command"] = "su -c reboot"
        self.assertFalse(valid("local-ai/intent-plan.schema.json", plan))
        plan = fixture(self.PLAN)
        plan["invocations"][0]["shell"] = "rm -rf /"
        self.assertFalse(valid("local-ai/intent-plan.schema.json", plan))

    def test_tool_ids_are_names_not_paths_or_commands(self):
        for bad in ("/system/bin/sh", "core.health;reboot", "Core.Health", "../x", ""):
            plan = fixture(self.PLAN)
            plan["invocations"][0]["tool_id"] = bad
            self.assertFalse(valid("local-ai/intent-plan.schema.json", plan), bad)

    def test_unknown_tools_and_bad_arguments_fail_closed(self):
        tools = fixture(self.TOOLS)
        plan = fixture(self.PLAN)
        self.assertEqual([], zsdk.invocation_errors(plan, tools))
        plan["invocations"].append({"invocation_id": "i-9", "tool_id": "sysfs.write", "arguments": {}})
        self.assertTrue(zsdk.invocation_errors(plan, tools))
        plan = fixture(self.PLAN)
        plan["invocations"] = [{"invocation_id": "i-1", "tool_id": "fas.set_profile", "arguments": {"profile": "turbo"}}]
        self.assertTrue(zsdk.invocation_errors(plan, tools))
        plan["invocations"][0]["arguments"] = {"profile": "balanced", "path": "/sys/x"}
        self.assertTrue(zsdk.invocation_errors(plan, tools))
        plan["invocations"][0]["arguments"] = {"profile": "balanced"}
        self.assertEqual([], zsdk.invocation_errors(plan, tools))

    def test_system_tools_go_through_core_with_explicit_confirmation(self):
        tools = fixture(self.TOOLS)
        sys_tool = next(t for t in tools if t["risk"] == "system")
        for change in ({"confirmation": "none"}, {"permission": "none"}):
            t = {**sys_tool, **change}
            self.assertFalse(valid("local-ai/tool-registry.schema.json", [t]), change)
        t = dict(sys_tool)
        del t["core_operation"]
        self.assertFalse(valid("local-ai/tool-registry.schema.json", [t]))

    def test_registry_semantics(self):
        tools = fixture(self.TOOLS)
        self.assertEqual([], zsdk.registry_errors(tools))
        self.assertTrue(zsdk.registry_errors(tools + [tools[0]]))
        open_params = copy.deepcopy(tools[0])
        open_params["parameters"] = {"type": "object"}
        self.assertTrue(zsdk.registry_errors([open_params]))

    def test_results_are_truthful(self):
        r = fixture("fixtures/synthetic/local-ai/execution-result-rejected.json")
        del r["error"]
        self.assertFalse(valid("local-ai/execution-result.schema.json", r))
        ok = {"invocation_id": "i-1", "tool_id": "fas.set_profile", "status": "applied_verified"}
        self.assertFalse(valid("local-ai/execution-result.schema.json", ok))
        ok["core_request_id"] = "r-1"
        self.assertTrue(valid("local-ai/execution-result.schema.json", ok))
        ok["status"] = "success"
        self.assertFalse(valid("local-ai/execution-result.schema.json", ok))

    def test_model_manifest_needs_https_pinned_revision_and_hashes(self):
        m = fixture("fixtures/synthetic/local-ai/model-manifest.json")
        for mutate in (lambda d: d["source"].update(url="http://example.invalid/m"),
                       lambda d: d["source"].update(revision="main"),
                       lambda d: d["files"][0].update(sha256="abc"),
                       lambda d: d["licenses"].pop("tokenizer")):
            bad = copy.deepcopy(m)
            mutate(bad)
            self.assertFalse(valid("local-ai/model-manifest.schema.json", bad))

    def test_approval_comes_only_once_and_explicitly(self):
        a = fixture("fixtures/synthetic/local-ai/user-approval.json")
        a["scope"] = "always"
        self.assertFalse(valid("local-ai/user-approval.schema.json", a))


if __name__ == "__main__":
    unittest.main()
