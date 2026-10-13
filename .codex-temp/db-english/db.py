import json, os, re, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MYSQL = Path('E:/localhost/xampp/mysql/bin/mysql.exe')
secret_file = Path('C:/Users/edoga/AppData/Roaming/Microsoft/UserSecrets/8440d348-7540-4d65-b3c0-00df83ab0560/secrets.json')
secrets = json.loads(secret_file.read_text(encoding='utf-8-sig'))
connection = secrets.get('ConnectionStrings:DefaultConnection') or secrets.get('ConnectionStrings', {}).get('DefaultConnection')
if not connection:
    raise RuntimeError('DefaultConnection was not found; no credentials printed.')
parts = {}
for item in connection.split(';'):
    if '=' in item:
        key, value = item.split('=',1)
        parts[key.strip().lower()] = value.strip()
database = parts.get('database', parts.get('initial catalog'))
if database != 'classhub_db':
    raise RuntimeError('Connection targets a different database; stopped.')

def run(sql=None, dump=False):
    def escape(value):
        return '"' + value.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r') + '"'
    values = {'host':parts.get('server',parts.get('host','localhost')), 'port':parts.get('port','3306'),
        'user':parts.get('user',parts.get('user id',parts.get('uid','root'))),
        'password':parts.get('password',parts.get('pwd',''))}
    name=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',suffix='.cnf',delete=False,encoding='utf-8') as f:
            name=f.name
            f.write('[client]\n'+'\n'.join(k+'='+escape(v) for k,v in values.items())+'\n')
        exe=MYSQL.with_name('mysqldump.exe') if dump else MYSQL
        args=[str(exe),'--defaults-extra-file='+name,'--default-character-set=utf8mb4']
        args += ['--single-transaction','--routines','--triggers','--events',database] if dump else ['--batch','--raw','--skip-column-names',database]
        result=subprocess.run(args,input=None if dump else sql,text=True,encoding='utf-8',capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.replace(values['password'],'[redacted]') if values['password'] else result.stderr)
        return result.stdout
    finally:
        if name: Path(name).unlink(missing_ok=True)

def audit():
    print('Server:',run('SELECT VERSION();').strip())
    tables=run("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME;").splitlines()
    snapshot={}
    for table in tables:
        ddl=run('SHOW CREATE TABLE `'+table+'`;').split('\t',1)[1].strip()
        snapshot[table]={'ddl':ddl,'count':int(run('SELECT COUNT(*) FROM `'+table+'`;').strip())}
        print(table, 'rows='+str(snapshot[table]['count']))
    dependencies=run("SELECT 'VIEW', TABLE_NAME FROM information_schema.VIEWS WHERE TABLE_SCHEMA=DATABASE(); SELECT 'TRIGGER', TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE(); SELECT 'ROUTINE', ROUTINE_NAME FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE(); SELECT 'EVENT', EVENT_NAME FROM information_schema.EVENTS WHERE EVENT_SCHEMA=DATABASE();")
    print('Dependencies:', dependencies.strip() or 'none')
    (ROOT/'schema-before.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'dependencies.txt').write_text(dependencies,encoding='utf-8')

if __name__=='__main__': audit()
