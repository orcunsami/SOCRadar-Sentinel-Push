"""Remove a plain-text lexer or its safety envelope; each must turn the test red."""
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
path=root/'azuredeploy.json'
original=path.read_text()
mutations=[('lexer removed',lambda q:q.replace('extract_all(@"\\x22', 'extract_all(@"BROKEN')),
           ('mv-apply grammar removed',lambda q:q.replace('mv-apply with_itemindex=TokenIndex Token = ContentTokens to typeof(dynamic) on (', 'mv-apply Token = ContentTokens on (')),
           ('json decode removed',lambda q:q.replace('parse_json(strcat("\\\"", StringInner, "\\\""))', 'tostring(StringInner)')),
           ('key newline guard removed',lambda q:q.replace(', "\\n", " ")', ', "\\n", "")')),
           ('native type encoding removed',lambda q:q.replace('dynamic_to_json(pack_array(AlarmContent[ContentKey]))', 'tostring(AlarmContent[ContentKey])')),
           ('exponent scalar removed',lambda q:q.replace('(?:[eE][+-]?\\d+)?', '')),
           ('empty string token lost',lambda q:q.replace('Punctuation in ("}", "]"), iff(Depth == 0, "", ")"),\n            "-")', 'Punctuation in ("}", "]"), iff(Depth == 0, "", ")"),\n            ""')),
           ('root comma separator broken',lambda q:q.replace('iff(RootKind == "array", ", ", "; ")', '", "')),
           ('nested group broken',lambda q:q.replace('iff(Depth == 1, "", "(")', '""')),
           ('fallback 1000 removed',lambda q:q.replace('substring(DescriptionBody, 0, 1000)', 'substring(DescriptionBody, 0, 4800)')),
           ('serialize removed',lambda q:q.replace('| serialize', '')),
           ('closing delta removed',lambda q:q.replace('Punctuation in ("}", "]"), -1', 'Punctuation in ("}", "]"), 0')),
           ('byte count replaced',lambda q:q.replace('strlen(base64_encode_tostring(DescriptionBody)) * 3 / 4', 'strlen(DescriptionBody)')),
           ('value newline guard removed',lambda q:q.replace('"\\n", "; "', '"\\n", ""')),
           ('byte reserve removed',lambda q:q.replace('BodyBudget / BodyBytes) - 10', 'BodyBudget / BodyBytes) + 500')),
           ('cell cap removed',lambda q:q.replace('strlen(ContentValue) > 300', 'strlen(ContentValue) > 99999')),
           ('content cap removed',lambda q:q.replace(')), 0, 2600)', ')), 0, 99999)')),
           ('details cap removed',lambda q:q.replace('"), 0, 1500)', '"), 0, 99999)')),
           ('no details fallback removed',lambda q:q.replace('coalesce(DetailsText, "No details")', 'DetailsText')),
           ('detail carriage return guard removed',lambda q:q.replace('replace_string(AlarmText, "\\r", "")', 'AlarmText')),
           ('long link cap removed',lambda q:q.replace('FullDescriptionLinkBytes > 768', 'FullDescriptionLinkBytes > 999999')),
           ('body budget clamp removed',lambda q:q.replace('max_of(0, 4800 - DescriptionLinkBytes)', '4800 - DescriptionLinkBytes')),
           ('byte guard removed',lambda q:q.replace('> 4900','> 99999'))]
blind=[]
try:
    for name, mutate in mutations:
        template=json.loads(original)
        resource=next(r for r in template['resources'] if r.get('kind')=='NRT')
        before=resource['properties']['query']
        resource['properties']['query']=mutate(before)
        if resource['properties']['query']==before:
            raise RuntimeError('No mutation: '+name)
        path.write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n')
        result=subprocess.run([sys.executable,str(root/'tests/test_alert_description.py')],capture_output=True,text=True,
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),timeout=60)
        print(('BLIND ' if result.returncode==0 else 'caught ')+name)
        if result.returncode==0: blind.append(name)
finally:
    path.write_text(original)
print('blind:',len(blind),'of',len(mutations))
sys.exit(bool(blind))
