import sys,json,tempfile
from pathlib import Path
sys.path.insert(0,'.codex-temp/db-english')
from db import run
task=Path('.codex-temp/assets')
resume = 'usage_scope' in run('SHOW COLUMNS FROM equipment;')
before=run('SELECT id,name,quantity,`condition`,note,room_id FROM equipment ORDER BY id;')
if not resume:
    backup=Path(tempfile.mkdtemp(prefix='classhub-assets-'))/'before.sql'
    backup.write_text(run(dump=True),encoding='utf-8')
    (task/'backup-path.txt').write_text(str(backup),encoding='utf-8')
    run(Path('docs/database/assets-inventory.sql').read_text(encoding='utf-8'))
else:
    backup=Path((task/'backup-path.txt').read_text(encoding='utf-8'))
    assert backup.exists()
    assert 'fk_equipment_room' not in run('SHOW CREATE TABLE equipment;'), 'Migration already complete.'
    run('ALTER TABLE equipment DROP FOREIGN KEY fk_thietbi_phong, ADD CONSTRAINT fk_equipment_room FOREIGN KEY (room_id) REFERENCES room(id) ON DELETE RESTRICT;')
assert run('SELECT id,name,quantity,`condition`,note,room_id FROM equipment ORDER BY id;')==before
assert run("SELECT COUNT(*) FROM equipment WHERE usage_scope<>'CABINET' OR catalog_code IS NULL OR version<>1;").strip()=='0'
print(json.dumps({'existing_equipment_preserved':len(before.splitlines()),'new_tables':0,'backup':str(backup)}))
