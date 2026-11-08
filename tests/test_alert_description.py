"""Pin Defender plain-text formatting and the existing alert safety envelope."""
import json
from pathlib import Path
import unittest

TEMPLATE = Path(__file__).resolve().parents[1] / 'azuredeploy.json'

class AlertDescriptionTests(unittest.TestCase):
    def test_both_rule_kinds_use_plain_text(self):
        template = json.loads(TEMPLATE.read_text())
        rules = [r for r in template['resources'] if r.get('kind') in ('Scheduled', 'NRT')]
        self.assertEqual({r['kind'] for r in rules}, {'Scheduled','NRT'})
        formatting = []
        for rule in rules:
            with self.subTest(kind=rule['kind']):
                p=rule['properties']
                q=p['query']
                self.assertNotIn('| Field | Value |',q)
                self.assertNotIn('Markdown',q)
                self.assertIn('strcat(PlainKey, ": ",',q)
                self.assertIn('strcat_array(ContentRows, "\\n")',q)
                self.assertNotIn('"\\\\|"',q)
                self.assertIn('BodyBudget = 4800 - 2 * strlen(DescriptionLink)',q)
                self.assertIn('> 4900',q)
                self.assertIn('DescriptionLink = strcat("View in SOCRadar: ", AlarmUrl)',q)
                self.assertEqual(p['alertDetailsOverride']['alertDescriptionFormat'],'{{AlarmDescription}}')
                self.assertIn('toupper(Status) == "OPEN"',q)
                self.assertIn('"connection.test"',q)
                formatting.append(q[q.index('| extend AlarmContent'):q.index('| project TimeGenerated')])
        self.assertEqual(formatting[0],formatting[1])

if __name__=='__main__':
    unittest.main()
