#!/usr/bin/env python3
"""Check the delivery, rollback, and CI promises exposed to operators."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/checks.yml").read_text(encoding="utf-8")
SETUP = (ROOT / "docs/setup-guide.md").read_text(encoding="utf-8")
STABLE_SHA = "d887b39123f95171f54adb2b9965b69c6b4c9314"


def require(text, description):
    if text not in README:
        raise AssertionError("README missing: %s" % description)


require("`key: value`", "plain description format")
require("If your installation currently uses `SOCRadar_Alarms_CL`, use this migration path", "actionable migration path")
require("input stream and SOCRadar form fields are unchanged", "migration input compatibility")
require("new workbook starts empty", "migration workbook history limitation")
require("Update your own KQL queries to `SOCRadar_Push_Alarms_CL`", "migration query step")
require("When the first real alarm arrives, verify one row in the new table, one incident, and no duplicate incident", "migration verification step")
require("CCF pull in the same workspace", "CCF shared-workspace warning")
require("GUID seeds are deliberately unchanged", "CCF GUID-seed decision")
require(STABLE_SHA, "fixed rollback revision")
require("raw.githubusercontent.com%2Forcunsami%2FSOCRadar-Sentinel-Push", "fixed rollback deployment URL")
require("Do not delete `SOCRadar_Alarms_CL`", "shared legacy table preservation")
require("dedicated to this Push installation", "reused app-registration warning")
require("very long alarm URL is omitted with an explicit marker", "long-URL omission behavior")
require("mixed UTF-8 tail", "mixed-tail content limitation")
require("tenant-specific validation", "unmeasured visual-rendering limitation")
require("A closed incident is not reopened; a new one opens.", "declared closed-incident resend limit")
require("sees rows from 12 minutes to 1 day old", "declared queryPeriod limit")
require("does not get one later", "declared expired backstop limit")

for name, document, heading in (
    ("README", README, "## 1. Register an application"),
    ("setup guide", SETUP, "## 1.0 App registrations"),
):
    section = document.split(heading, 1)[1].split("\n## ", 1)[0]
    for text in ("**All applications**", "filter by name", "SOCRadar Push/DCR",
                 "Reuse a suitable registration in your tenant", "Application (client) ID",
                 "Directory (tenant) ID", "service principal's Object ID",
                 "stored", "unexpired", "**same app registration**",
                 "Only if no suitable registration exists", "**New registration**"):
        if text not in section:
            raise AssertionError("%s missing reuse-first instruction: %s" % (name, text))
    if section.index("**All applications**") > section.index("**New registration**"):
        raise AssertionError("%s offers new registration before reuse search" % name)

if "Field | Value table" in README or "AlertBacked" in README:
    raise AssertionError("README retains superseded description or internal-table wording")
if "candidate" in README.lower() or "21861" in README:
    raise AssertionError("README retains internal candidate wording")
for output in ("dceUri", "dcrImmutableId", "tenantId"):
    require("`%s`" % output, "exact deployment output name " + output)
if 'branches: [master, main, "e2e-*"]' not in WORKFLOW:
    raise AssertionError("checks workflow does not include the permanent e2e branch policy")
if "python3 tests/mutate_description.py" not in WORKFLOW:
    raise AssertionError("checks workflow does not run description mutations")

print("delivery documentation and checks workflow contract passed")
