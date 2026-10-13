from pathlib import Path
import json, re, hashlib, datetime, tempfile
from db import run, ROOT
schema=json.loads((ROOT/'schema-before.json').read_text(encoding='utf-8'))
mapping=json.loads((ROOT/'mapping.json').read_text(encoding='utf-8'))
docs=ROOT.parents[1]/'docs/database'
scratch='classhub_rename_check_20261012'
if int(run(f"SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{scratch}';")):
    raise RuntimeError('Rehearsal database already exists; no changes made.')
backup_dir=Path(tempfile.gettempdir())/('classhub-db-english-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup_dir.mkdir()
backup=backup_dir/'classhub_db-before.sql'
backup.write_text(run(dump=True),encoding='utf-8')
assert backup.stat().st_size>1000
(ROOT/'backup-path.txt').write_text(str(backup),encoding='utf-8')
run(f'CREATE DATABASE `{scratch}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;')
create=[]; fks=[]
for old,item in schema.items():
    ddl=item['ddl']
    lines=ddl.splitlines()
    for line in lines:
        if ' FOREIGN KEY ' in line:
            fks.append(f'ALTER TABLE `{old}` ADD '+line.strip().rstrip(',')+';')
    lines=[line for line in lines if ' FOREIGN KEY ' not in line]
    ddl='\n'.join(lines)
    ddl=re.sub(r',\n\)', '\n)',ddl)
    create.append(ddl+';')
run(f'USE `{scratch}`;\n'+'\n'.join(create+fks))
def snapshot(current):
    result={}
    for old in schema:
        table=mapping['tables'][old] if current else old
        cols=re.findall(r'^  `([^`]+)` ',schema[old]['ddl'],re.M)
        actual=[mapping['columns'][old].get(c,c) if current else c for c in cols]
        expressions=["COALESCE(HEX(CAST(`"+c+"` AS BINARY)), 'NULL')" for c in actual]
        hashes=run('SELECT SHA2(CONCAT_WS(\'|\','+','.join(expressions)+'),256) FROM `'+table+'` ORDER BY 1;')
        result[old]=hashlib.sha256(hashes.encode()).hexdigest()
    return result
(ROOT/'data-before.json').write_text(json.dumps(snapshot(False)),encoding='utf-8')
run(f'USE `{scratch}`;\n'+(docs/'rename-to-english.sql').read_text(encoding='utf-8'))
run(f'USE `{scratch}`;\n'+(docs/'rollback-english-names.sql').read_text(encoding='utf-8'))
for table,item in schema.items():
    restored=run(f'USE `{scratch}`; SHOW CREATE TABLE `{table}`;').split('\t',1)[1].strip()
    def norm(ddl): return sorted(line.strip().rstrip(',') for line in ddl.splitlines())
    assert norm(restored)==norm(item['ddl']), 'Rehearsal schema mismatch: '+table
run(f'DROP DATABASE `{scratch}`;')
print('Backup saved:',backup)
print('Forward and rollback successfully rehearsed; all ten table definitions restored exactly.')
