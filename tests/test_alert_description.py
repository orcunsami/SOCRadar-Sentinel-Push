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
                self.assertIn('extract_all(@"\\x22((?:\\\\.|[^\\x22\\\\])*)\\x22|([{}\\[\\],:])|',q)
                self.assertIn('mv-apply with_itemindex=TokenIndex Token = ContentTokens to typeof(dynamic) on (',q)
                self.assertIn('parse_json(strcat("\\\"", StringInner, "\\\""))',q)
                self.assertIn('PlainKey = replace_string(replace_string(replace_string(replace_string(ContentKey, "\\r", ""), "\\n", " "), "\\"", "”"), "_", " ")',q)
                self.assertIn('dynamic_to_json(pack_array(AlarmContent[ContentKey]))',q)
                self.assertIn('substring(ContentPacked, 1, strlen(ContentPacked) - 2)',q)
                self.assertIn('substring(ContentJson, 0, 6000)',q)
                self.assertIn('RootKind = gettype(AlarmContent[ContentKey])',q)
                self.assertIn('(?:[eE][+-]?\\d+)?',q)
                self.assertIn('isnotempty(StringInner), DecodedString',q)
                self.assertIn('Punctuation in ("}", "]"), iff(Depth == 0, "", ")"),\n            "-")',q)
                self.assertIn('replace_string(replace_string(replace_string(tostring(parse_json(',q)
                self.assertIn('Punctuation == ",", iff(RootKind == "array", ", ", "; ")',q)
                self.assertIn('Punctuation in ("{", "["), iff(Depth == 1, "", "(")',q)
                self.assertIn('Punctuation in ("}", "]"), iff(Depth == 0, "", ")")',q)
                self.assertIn('strcat(PlainKey, ": ",',q)
                self.assertIn('strcat_array(ContentRows, "\\n")',q)
                self.assertIn('strlen(ContentValue) > 300',q)
                self.assertIn('substring(ContentValue, 0, 300)',q)
                self.assertIn('substring(strcat("Content:\\n", strcat_array(ContentRows, "\\n")), 0, 2600)',q)
                self.assertIn('replace_string(AlarmText, "\\r", "")',q)
                self.assertIn('substring(replace_string(AlarmText, "\\r", ""), 0, 1500)',q)
                self.assertIn('coalesce(DetailsText, "No details")',q)
                self.assertNotIn('| Field | Value |',q)
                self.assertIn('FullDescriptionLinkBytes > 768',q)
                self.assertIn('View in SOCRadar: link omitted (URL too long)',q)
                self.assertIn('BodyBudget = max_of(0, 4800 - DescriptionLinkBytes)',q)
                self.assertIn('> 4900',q)
                self.assertIn('FullDescriptionLink = strcat("View in SOCRadar: ", AlarmUrl)',q)
                self.assertEqual(p['alertDetailsOverride']['alertDescriptionFormat'],'{{AlarmDescription}}')
                self.assertIn('toupper(Status) == "OPEN"',q)
                self.assertIn('"connection.test"',q)
                formatting.append(q[q.index('| extend AlarmContent'):q.index('| project TimeGenerated')])
        self.assertEqual(formatting[0],formatting[1])

    def test_content_golden_cases_are_live_engine_fixtures_not_a_python_formatter(self):
        fixtures = Path(__file__).resolve().parent / 'fixtures' / 'alert_description_content.json'
        cases = json.loads(fixtures.read_text())
        self.assertEqual(
            {case['name'] for case in cases},
            {'array', 'object', 'nested', 'empty', 'scalars', 'quotes_and_punctuation', 'escaped_backslash_and_quote',
             'literal_json_looking_string', 'newline', 'exponent_array', 'null_and_empty_string', 'newline_key'},
        )
        by_name = {case['name']: case for case in cases}
        self.assertEqual(by_name['array']['expected'], 'tags: sentetik, örnek')
        self.assertEqual(by_name['object']['expected'], 'evidence: source: test; value: bir | iki')
        self.assertEqual(by_name['empty']['expected'], 'empty array: -; empty object: -')
        self.assertEqual(by_name['scalars']['expected'], 'count: 42; enabled: true')
        self.assertEqual(by_name['quotes_and_punctuation']['expected'], 'note: tırnak ”iç” ve virgül, brace { korunur')
        self.assertEqual(by_name['escaped_backslash_and_quote']['expected'], 'note: tırnak \\”iç\\” korunur')
        self.assertEqual(by_name['literal_json_looking_string']['expected'], 'note: [literal]')
        self.assertEqual(by_name['newline']['expected'], 'note: ilk; ikinci')
        self.assertEqual(by_name['exponent_array']['expected'], 'values: 1e100, -0.0025')
        self.assertEqual(by_name['null_and_empty_string']['expected'], 'none: -; blank: -')
        self.assertEqual(by_name['newline_key']['expected'], 'line key: value')

if __name__=='__main__':
    unittest.main()
