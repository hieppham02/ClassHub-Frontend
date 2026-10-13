from pathlib import Path
p=Path('.codex-temp/assets/backend/Controllers/AssetsController.cs')
s=p.read_text(encoding='utf-8')
s=s.replace('bool online=n.DataSource!="MOCK" && n.Status=="ONLINE" && last.HasValue\n                && (now-DateTime.SpecifyKind(last.Value,DateTimeKind.Utc)).TotalSeconds<=Math.Max(90,n.PublishIntervalSeconds*3);', '''// Explicit demo connectivity is stored separately from actual measurement freshness.
            bool online=n.Status=="ONLINE" && (n.DataSource=="MOCK" || (last.HasValue
                && (now-DateTime.SpecifyKind(last.Value,DateTimeKind.Utc)).TotalSeconds<=Math.Max(90,n.PublishIntervalSeconds*3)));''')
p.write_text(s,encoding='utf-8')
import sys
sys.path.insert(0,'.codex-temp/db-english')
from db import run
ids=run("SELECT id FROM iot_node WHERE data_source='MOCK' AND status='OFFLINE' ORDER BY room_id,id LIMIT 4;").splitlines()
assert all(i.isdigit() for i in ids)
if ids:
    run("UPDATE iot_node SET status='ONLINE' WHERE id IN ("+','.join(ids)+") AND data_source='MOCK' AND status='OFFLINE';")
print(run('SELECT room_id,status FROM iot_node ORDER BY room_id;'))
