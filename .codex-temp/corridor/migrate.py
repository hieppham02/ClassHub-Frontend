import sys, os, subprocess
from pathlib import Path
sys.path.insert(0, '.codex-temp/db-english')
from db import run

sql = Path('docs/database/corridor-cabinets.sql').read_text(encoding='utf-8')
test_database = 'classhub_corridor_check'
if '--apply' in sys.argv:
    run(sql)
    invalid = int(run("SELECT COUNT(*) FROM room r JOIN cabinet c ON c.room_id=r.id WHERE r.id LIKE 'STANDARD-%' AND (r.name NOT REGEXP CONCAT('^',r.building_id,'-',r.floor,'[0-9]{2}$') OR c.name<>r.name);").strip())
    assert invalid == 0, 'Room/cabinet names are inconsistent'
    print('PASS: database room and cabinet names follow building-floor-room naming.')
    print(run("SELECT location_type,COUNT(*) FROM room GROUP BY location_type; SELECT COUNT(*) FROM cabinet c JOIN room r ON r.id=c.room_id WHERE r.location_type='CORRIDOR';"))
else:
    # Only a dedicated scratch database is created/deleted; application data stays intact.
    exists = run(f"SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{test_database}';").strip()
    if exists != '0':
        raise RuntimeError('Scratch database already exists; stopped.')
    run(f'CREATE DATABASE `{test_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;')
    try:
        statements = [f'USE `{test_database}`;', 'SET FOREIGN_KEY_CHECKS=0;']
        tables = run("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE';").splitlines()
        for table in tables:
            ddl = run(f'SHOW CREATE TABLE `{table}`;').split('\t', 1)[1]
            statements.append(ddl + ';')
            if table != 'audit_log':
                columns = run(f"SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND EXTRA NOT LIKE '%GENERATED%' ORDER BY ORDINAL_POSITION;").splitlines()
                names = ','.join('`' + column + '`' for column in columns)
                statements.append(f'INSERT INTO `{table}` ({names}) SELECT {names} FROM classhub_db.`{table}`;')
        statements.append('SET FOREIGN_KEY_CHECKS=1;')
        run('\n'.join(statements))
        run(f'USE `{test_database}`;\n' + sql)
        before = run(f'USE `{test_database}`; SELECT COUNT(*) FROM room; SELECT COUNT(*) FROM cabinet; SELECT COUNT(*) FROM equipment;')
        run(f'USE `{test_database}`;\n' + sql)
        after = run(f'USE `{test_database}`; SELECT COUNT(*) FROM room; SELECT COUNT(*) FROM cabinet; SELECT COUNT(*) FROM equipment;')
        assert before == after, 'Migration is not idempotent'
        expected = int(run(f'USE `{test_database}`; SELECT SUM(COALESCE(floor_count,1)) FROM building;').strip())
        actual = int(run(f"USE `{test_database}`; SELECT COUNT(*) FROM room WHERE location_type='CORRIDOR';").strip())
        assert actual == expected, (actual, expected)
        standard = int(run(f"USE `{test_database}`; SELECT COUNT(*) FROM room r JOIN cabinet c ON c.room_id=r.id WHERE r.id LIKE 'STANDARD-%';").strip())
        assert standard == expected * 5, (standard, expected * 5)
        try:
            run(f"USE `{test_database}`; INSERT INTO room (id,name,floor,capacity,status,building_id,location_type) SELECT 'CHECK-DUPLICATE-CORRIDOR','Tủ tự do',floor,0,status,building_id,location_type FROM room WHERE location_type='CORRIDOR' LIMIT 1;")
        except RuntimeError:
            print('PASS: database rejects a second corridor cabinet on the same floor.')
        else:
            raise AssertionError('Database allowed a second corridor cabinet on one floor')
        print(f'PASS: {standard} additional ordinary cabinets, five per floor.')
        print(f'PASS: {actual} corridor cabinets, one per floor; migration rerun leaves counts unchanged.')
        if '--test-api' in sys.argv:
            env = os.environ.copy(); env['CLASSHUB_CORRIDOR_TEST_DB'] = test_database
            result = subprocess.run(['dotnet', '.codex-temp/corridor/integration-build/integration.dll'], env=env)
            if result.returncode: raise RuntimeError('API integration checks failed')
    finally:
        run(f'DROP DATABASE `{test_database}`;')
