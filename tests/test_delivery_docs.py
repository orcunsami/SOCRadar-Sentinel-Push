#!/usr/bin/env python3
"""Check the delivery, rollback, and CI promises exposed to operators."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/checks.yml").read_text(encoding="utf-8")
STABLE_SHA = "d887b39123f95171f54adb2b9965b69c6b4c9314"


def require(text, description):
    if text not in README:
        raise AssertionError("README missing: %s" % description)


require("`key: value`", "plain description format")
require("CCF pull in the same workspace", "CCF shared-workspace warning")
require("GUID seeds are deliberately unchanged", "CCF GUID-seed decision")
require(STABLE_SHA, "fixed rollback revision")
require("raw.githubusercontent.com%2Forcunsami%2FSOCRadar-Sentinel-Push", "fixed rollback deployment URL")
require("Do not delete `SOCRadar_Alarms_CL`", "shared legacy table preservation")
require("dedicated to this Push installation", "reused app-registration warning")
require("very long alarm URL is omitted with an explicit marker", "long-URL omission behavior")
require("mixed UTF-8 tail", "mixed-tail content limitation")
require("tenant-specific validation", "unmeasured visual-rendering limitation")

if "Field | Value table" in README or "AlertBacked" in README:
    raise AssertionError("README retains superseded description or internal-table wording")
if "branches: [master, main, e2e-push-0111]" not in WORKFLOW:
    raise AssertionError("checks workflow does not include e2e-push-0111")
if "python3 tests/mutate_description.py" not in WORKFLOW:
    raise AssertionError("checks workflow does not run description mutations")

print("delivery documentation and checks workflow contract passed")
