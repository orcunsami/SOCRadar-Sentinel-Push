#!/usr/bin/env python3
"""Check the delivery, rollback, and CI promises exposed to operators."""

from pathlib import Path
import json
import re
from urllib.parse import unquote


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
require("They share GUID seeds", "CCF GUID collision reason")
require("Do not combine these installations during an upgrade or rollback", "CCF migration safety boundary")
require(STABLE_SHA, "fixed rollback revision")
require("raw.githubusercontent.com%2Forcunsami%2FSOCRadar-Sentinel-Push", "fixed rollback deployment URL")
require("Do not delete `SOCRadar_Alarms_CL`", "shared legacy table preservation")
require("dedicated to this Push installation", "reused app-registration warning")
require("very long alarm URL is omitted with an explicit marker", "long-URL omission behavior")
require("mixed UTF-8 tail", "mixed-tail content limitation")
require("Check the description and source link in your incident", "customer visual-rendering and destination check")
limits = README.split("## Things to know\n", 1)[1].split("\n## ", 1)[0]
for phrase in ("A closed incident is not reopened; a new one opens.",
               "sees rows from 12 minutes to 1 day old", "does not get one later",
               "within 7 days", "every 10 minutes"):
    if phrase not in limits:
        raise AssertionError("LIMIT:documentation")

template = json.loads((ROOT / "azuredeploy.json").read_text())
upgrade = README.split("### Updating an existing Push installation\n", 1)[1].split("\n## ", 1)[0]
for phrase in ("two analytic rules can fail with `One of the tables does not exist`",
               "Only for that error, wait until `SOCRadar_Push_Alarms_CL | take 0` succeeds in Logs",
               "redeploy the same template once more with the same values",
               "For any other error, or if this retry fails, stop"):
    if phrase not in upgrade:
        raise AssertionError("LIMIT:upgrade-retry")
rules = [r for r in template["resources"] if r.get("kind") in ("Scheduled", "NRT")]
if len(rules) != 2 or {r["kind"] for r in rules} != {"Scheduled", "NRT"}:
    raise AssertionError("LIMIT:rule-kinds")
for rule in rules:
    properties = rule["properties"]
    if rule["kind"] == "Scheduled":
        for field, expected in (("queryPeriod", "P1D"), ("queryFrequency", "PT10M")):
            if properties.get(field) != expected:
                raise AssertionError("LIMIT:" + field)
    elif any(field in properties for field in ("queryPeriod", "queryFrequency")):
        raise AssertionError("LIMIT:nrt-cadence")
    grouping = properties["incidentConfiguration"]["groupingConfiguration"]
    if grouping.get("reopenClosedIncident") is not False:
        raise AssertionError("LIMIT:reopenClosedIncident")
    if grouping.get("lookbackDuration") != "P7D":
        raise AssertionError("LIMIT:lookbackDuration")

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
for output in ("DceUri", "DcrImmutableId", "StreamName", "TenantId", "LogIngestionUrl"):
    if output not in template["outputs"]:
        raise AssertionError("Unknown deployment output " + output)
    for name, document in (("README", README), ("setup guide", SETUP)):
        if not re.search(r"\b" + re.escape(output) + r"\b", document):
            raise AssertionError(name + " missing canonical output " + output)
for parameter in ("WorkspaceName", "DeployNewWorkspace", "WorkspaceLocation",
                  "ServicePrincipalObjectId", "TableRetentionDays"):
    if parameter not in template["parameters"]:
        raise AssertionError("Unknown deployment parameter " + parameter)
    for name, document in (("README", README), ("setup guide", SETUP)):
        if "`%s`" % parameter not in document:
            raise AssertionError(name + " missing canonical parameter " + parameter)

for document in (README, SETUP):
    assert not re.search(r"video|recording|preprod|Postman|off camera|demo workspace|we looked|synthetic|greenfield|task_azure|E2E", document, re.I), "Customer docs retain internal process language"
    assert not re.search(r"[ğşıİöüç—]", document), "Customer docs must use English without em dash"
    for phrase in ("4000 UTF-16", "connection.test", "Monitoring Metrics Publisher"):
        assert phrase in document, "Missing customer safety instruction: " + phrase
require("HTTP 204 alone is not end-to-end ingestion proof", "HTTP acknowledgement boundary")
require("A separate incident per alarm is not guaranteed", "URL grouping boundary")
deploy = re.search(r"\[!\[Deploy to Azure\].*?\]\((https://portal.azure.com/[^)]+)\)", README)
assert deploy, "Customer Deploy button missing"
assert unquote(deploy.group(1)).endswith("/orcunsami/SOCRadar-Sentinel-Push/master/azuredeploy.json"), "Customer Deploy button must use master"
registration = README.split("## 1. Register an application\n", 1)[1].split("\n## ", 1)[0]
steps = dict(re.findall(r"(?m)^([1-4])\. (.+)$", registration))
assert set(steps) == {"1", "2", "3", "4"}, "Application registration steps missing"
assert "Application (client) ID" in steps["2"] and "Directory (tenant) ID" in steps["2"], "step 1.2 must provide identity values"
assert "secret" in steps["3"] and "Value" in steps["3"], "step 1.3 must provide secret Value"
assert "Object ID" in steps["4"] and "service principal" in steps["4"], "step 1.4 must provide service principal Object ID"
if 'branches: [master, main, "e2e-*", "armttk0-0116"]' not in WORKFLOW:
    raise AssertionError("checks workflow does not include the permanent e2e branch policy")
if 'ARM-TTK must have zero failures' not in WORKFLOW or 'tests/check_arm_ttk.ps1' not in WORKFLOW:
    raise AssertionError("checks workflow does not enforce ARM-TTK")
if "python3 tests/mutate_description.py" not in WORKFLOW:
    raise AssertionError("checks workflow does not run description mutations")
if "python3 tests/mutate_limits.py" not in WORKFLOW:
    raise AssertionError("checks workflow does not run documented-limit mutations")

print("delivery documentation and checks workflow contract passed")
