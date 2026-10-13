from pathlib import Path
import re
root=Path(__file__).resolve().parents[2]/'docs/database'
for name in ['rename-to-english.sql','rollback-english-names.sql']:
    p=root/name
    output=[];table=None;clauses=[]
    for line in p.read_text(encoding='utf-8').splitlines():
        m=re.match(r'ALTER TABLE (`[^`]+`) (.*);$',line)
        if m and m[1]==table:
            clauses.append(m[2]);continue
        if table:output.append('ALTER TABLE '+table+'\n    '+',\n    '.join(clauses)+';')
        table=m[1] if m else None
        clauses=[m[2]] if m else []
        if not m:output.append(line)
    if table:output.append('ALTER TABLE '+table+'\n    '+',\n    '.join(clauses)+';')
    p.write_text('\n'.join(output)+'\n',encoding='utf-8')
