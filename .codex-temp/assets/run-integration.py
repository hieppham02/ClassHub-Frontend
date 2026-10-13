import os,re,subprocess,sys,time
sys.path.insert(0,'.codex-temp/db-english')
from db import run
database='classhub_assets_test_'+str(int(time.time()))
assert re.fullmatch(r'classhub_assets_test_\d+',database)
tables=run("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME;").splitlines()
statements=['CREATE DATABASE `'+database+'` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;','USE `'+database+'`;','SET FOREIGN_KEY_CHECKS=0;']
for table in tables:
    ddl=run('SHOW CREATE TABLE `'+table+'`;').split('\t',1)[1].strip()
    statements.append(ddl+';')
for table in tables:
    if table!='audit_log': statements.append('INSERT INTO `'+table+'` SELECT * FROM classhub_db.`'+table+'`;')
statements.append('SET FOREIGN_KEY_CHECKS=1;')
run('\n'.join(statements))
try:
    env=os.environ.copy();env['CLASSHUB_ASSET_TEST_DB']=database
    result=subprocess.run(['dotnet','.codex-temp/assets/integration-build/integration.dll'],env=env,capture_output=True,text=True,encoding='utf-8')
    print(result.stdout)
    if result.returncode:
        safe=re.sub(r'(?i)(password|pwd)=[^;\s]*', r'\1=[redacted]',result.stderr)
        print(safe[:3000])
    if result.returncode:
        # Do not print arbitrary errors that might include the database connection string.
        print('Integration run failed; inspect the assertion output.');sys.exit(result.returncode)
finally:
    assert database.startswith('classhub_assets_test_') and database!='classhub_db'
    run('DROP DATABASE `'+database+'`;')
