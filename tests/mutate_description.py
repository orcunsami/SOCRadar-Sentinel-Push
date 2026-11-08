"""Restore Markdown and remove the byte guard; each must turn the test red."""
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
path=root/'azuredeploy.json'
original=path.read_text()
mutations=[('markdown header',lambda q:q.replace('Content:', '| Field | Value |')),
           ('byte guard removed',lambda q:q.replace('> 4900','> 99999')),
           ('markdown pipe escape',lambda q:q.replace('strcat(PlainKey,', 'strcat("\\\\|", PlainKey,'))]
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
