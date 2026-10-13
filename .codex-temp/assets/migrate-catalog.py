from pathlib import Path
import sys,tempfile
sys.path.insert(0,'.codex-temp/db-english')
from db import run
backup=Path(tempfile.mkdtemp(prefix='classhub-catalog-'))/'before.sql'
backup.write_text(run(dump=True),encoding='utf-8')
Path('.codex-temp/assets/catalog-backup.txt').write_text(str(backup),encoding='utf-8')
run(Path('docs/database/equipment-catalog.sql').read_text(encoding='utf-8'))
print('Catalog migration applied; backup saved.')
print(run('SELECT COUNT(*),SUM(quantity) FROM equipment; SELECT COUNT(*) FROM equipment_catalog;'))
