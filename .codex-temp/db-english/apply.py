import json,re,hashlib,shutil,subprocess
from pathlib import Path
from db import run, ROOT

schema=json.loads((ROOT/'schema-before.json').read_text(encoding='utf-8'))
mapping=json.loads((ROOT/'mapping.json').read_text(encoding='utf-8'))
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
source=ROOT.parents[1].parent/'Backend/ClassHub-API/ClassHub-API'
docs=ROOT.parents[1]/'docs/database'
backup=Path((ROOT/'backup-path.txt').read_text(encoding='utf-8'))
assert backup.exists() and backup.stat().st_size>1000
assert (ROOT/'rehearsal-ok.txt').exists(), 'Rehearsal not complete'
for name,expected in manifest.items():
    p=source/name
    actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    assert actual==expected,'Backend changed since preparation: '+name
current=set(run("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE';").splitlines())
assert current==set(schema),'Live table names changed; stopped'

def checksum(renamed):
    result={}
    for old in schema:
        table=mapping['tables'][old] if renamed else old
        cols=re.findall(r'^  `([^`]+)` ',schema[old]['ddl'],re.M)
        actual=[mapping['columns'][old].get(c,c) if renamed else c for c in cols]
        expressions=["COALESCE(HEX(CAST(`"+c+"` AS BINARY)), 'NULL')" for c in actual]
        hashes=run('SELECT SHA2(CONCAT_WS(\'|\','+','.join(expressions)+'),256) FROM `'+table+'` ORDER BY 1;')
        result[old]=hashlib.sha256(hashes.encode()).hexdigest()
    return result

before=checksum(False)
assert before==json.loads((ROOT/'data-before.json').read_text(encoding='utf-8')), 'Data changed after backup/rehearsal; stopped'
for table in schema:
    actual=run('SHOW CREATE TABLE `'+table+'`;').split('\t',1)[1].strip()
    assert actual==schema[table]['ddl'],'Live schema changed: '+table
code_backup=backup.parent/'backend-before'
for name in manifest:
    if (source/name).exists():
        p=code_backup/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)

def invert(statement):
    if statement.startswith('RENAME TABLE'):
        return 'RENAME TABLE '+', '.join(f'`{new}` TO `{old}`' for old,new in mapping['tables'].items() if old!=new)+';'
    table=re.match(r'ALTER TABLE `([^`]+)`',statement)[1]
    old=next((o for o,n in mapping['tables'].items() if n==table),table)
    original=schema[old]['ddl']
    if ' DROP ' in statement:
        names=re.findall(r'DROP (?:FOREIGN KEY|CONSTRAINT) `([^`]+)`',statement)
        clauses=[]
        for name in names:
            constraint=next(line.strip().rstrip(',') for line in original.splitlines() if line.strip().startswith(f'CONSTRAINT `{name}`'))
            clauses.append('ADD '+constraint)
    elif 'CHANGE COLUMN' in statement:
        clauses=[]
        for a,b in re.findall(r'CHANGE COLUMN `([^`]+)` `([^`]+)`',statement):
            definition=re.search(r'^  `'+re.escape(a)+r'` (.*?)(?:,)?$',original,re.M)[1].rstrip(',')
            clauses.append(f'CHANGE COLUMN `{b}` `{a}` {definition}')
    else:
        clauses=['DROP '+('FOREIGN KEY' if ' FOREIGN KEY ' in constraint else 'CONSTRAINT')+' `'+re.match(r'CONSTRAINT `([^`]+)`',constraint)[1]+'`'
            for constraint in re.findall(r'ADD (CONSTRAINT .*?)(?=,\n    ADD |$)',statement,re.S)]
    assert clauses,'Cannot invert statement'
    return 'ALTER TABLE `'+table+'` '+', '.join(clauses)+';'

sql=(docs/'rename-to-english.sql').read_text(encoding='utf-8')
sql='\n'.join(line for line in sql.splitlines() if not line.startswith('--'))
statements=[s.strip() for s in sql.split(';') if s.strip()]
undo=[];copied=[]
try:
    for i,statement in enumerate(statements):
        reverse=invert(statement)
        run(statement+';')
        undo.append(reverse)
        (ROOT/'rollback-applied-steps.sql').write_text('\n'.join(reversed(undo)),encoding='utf-8')
        print(f'Applied schema step {i+1}/{len(statements)}',flush=True)
    assert checksum(True)==before,'Data checksum mismatch'
    test=subprocess.run(['dotnet',str(ROOT/'mapping-check/ClassHub-API.dll')],capture_output=True,text=True,encoding='utf-8')
    if test.returncode: raise RuntimeError('EF mapping check failed: '+test.stdout+test.stderr)
    print(test.stdout,flush=True)
    for name in manifest:
        shutil.copyfile(ROOT/'backend'/name,source/name);copied.append(name)
    (ROOT/'applied-ok.txt').write_text('Ten tables renamed, data checksums unchanged, EF reads verified, backend applied.',encoding='utf-8')
    print('Completed: data unchanged, foreign keys/checks restored, backend source synchronized.',flush=True)
except Exception:
    for name in copied:
        saved=code_backup/name
        if saved.exists():shutil.copyfile(saved,source/name)
        else:(source/name).unlink(missing_ok=True)
    for statement in reversed(undo):run(statement)
    print('Successfully applied schema steps reverted; inspect failure before retrying.',flush=True)
    raise
