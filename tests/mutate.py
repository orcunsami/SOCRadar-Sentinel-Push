#!/usr/bin/env python3
"""Break the template on purpose and prove the test notices.

Each entry breaks one invariant, runs the test that should catch it, and restores the file.
A mutation that survives is BLIND and the run exits non-zero.

    python3 tests/mutate.py
"""

import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = "azuredeploy.json"
P = "tests/test_workspace_precheck.py"
MUTATIONS = [
    ("workspace toggle defaults to true again", T,
     '''"DeployNewWorkspace": {
      "type": "bool",
      "defaultValue": false,''',
     '''"DeployNewWorkspace": {
      "type": "bool",
      "defaultValue": true,''', P),
    ("precheck evaluates in the parent scope", T,
     '''"expressionEvaluationOptions": {
          "scope": "inner"''',
     '''"expressionEvaluationOptions": {
          "scope": "outer"''', P),
    ("precheck no longer looks at the workspace", T,
     '''"value": "[reference(parameters('WorkspaceResourceId'), '2023-09-01', 'Full').properties.customerId]"''',
     '''"value": "none"''', P),
    ("precheck runs when the workspace is being created", T,
     '''"condition": "[not(parameters('DeployNewWorkspace'))]",
      "type": "Microsoft.Resources/deployments"''',
     '''"condition": "[true()]",
      "type": "Microsoft.Resources/deployments"''', P),
    ("the endpoint does not wait for the precheck", T,
     '''"networkAcls": {
          "publicNetworkAccess": "Enabled"
        }
      },
      "dependsOn": [
        "[resourceId('Microsoft.Resources/deployments', 'precheck-workspace-exists')]"
      ]''',
     '''"networkAcls": {
          "publicNetworkAccess": "Enabled"
        }
      },
      "dependsOn": []''', P),
    ("precheck stops asserting Microsoft Sentinel", T,
     '''"value": "[reference(extensionResourceId(parameters('WorkspaceResourceId'), 'Microsoft.SecurityInsights/onboardingStates', 'default'), '2023-02-01', 'Full').id]"''',
     '''"value": "none"''', P),
]


def syntax_error(path, text):
    if path.endswith(".json"):
        try:
            json.loads(text)
        except ValueError as e:
            return str(e)
    return None


blind = []
for name, path, old, new, test in MUTATIONS:
    full = os.path.join(REPO, path)
    orig = open(full, encoding="utf-8").read()
    if orig.count(old) != 1:
        print("SKIP  %-48s anchor found %d time(s) in %s" % (name, orig.count(old), path)); blind.append(name); continue
    mutant = orig.replace(old, new, 1)
    err = syntax_error(path, mutant)
    if err:
        print("FAKE  %-48s mutant does not parse: %s" % (name, err)); blind.append(name); continue
    try:
        open(full, "w", encoding="utf-8").write(mutant)
        r = subprocess.run([sys.executable, test], cwd=REPO, capture_output=True, text=True, timeout=120,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = None
    finally:
        open(full, "w", encoding="utf-8").write(orig)
    if rc is None:
        print("ERROR %-48s timed out, not a catch" % name); blind.append(name)
    elif rc == 0:
        print("BLIND %-48s still passed" % name); blind.append(name)
    else:
        print("caught %-47s" % name)
print("\nblind:", len(blind), "of", len(MUTATIONS))
sys.exit(1 if blind else 0)
