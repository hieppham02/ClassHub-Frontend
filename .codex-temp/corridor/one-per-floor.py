import sys
sys.path.insert(0, '.codex-temp/db-english')
from db import run

extra = "r.location_type='CORRIDOR' AND r.id LIKE '%-2'"
unsafe = run(f"""SELECT COUNT(*) FROM room r WHERE {extra} AND (
 EXISTS (SELECT 1 FROM borrowing_session b WHERE b.room_id=r.id)
 OR EXISTS (SELECT 1 FROM equipment e WHERE e.room_id=r.id)
 OR EXISTS (SELECT 1 FROM audit_log a WHERE a.details LIKE CONCAT('%',r.id,'%'))
 OR EXISTS (SELECT 1 FROM cabinet c WHERE c.room_id=r.id AND
 (c.is_online=1 OR c.lock_state<>'LOCKED' OR c.mac_address NOT LIKE 'UNCONFIGURED-%')));""").strip()
if unsafe != '0':
    raise RuntimeError('Extra cabinets have activity or configuration; stopped to preserve data.')
run(f"""START TRANSACTION;
DELETE c FROM cabinet c JOIN room r ON r.id=c.room_id WHERE {extra};
DELETE r FROM room r WHERE {extra};
UPDATE room SET name='Tủ tự do' WHERE location_type='CORRIDOR';
UPDATE cabinet c JOIN room r ON r.id=c.room_id SET c.name=r.name WHERE r.location_type='CORRIDOR';
COMMIT;""")
counts = run("SELECT building_id,floor,COUNT(*) FROM room WHERE location_type='CORRIDOR' GROUP BY building_id,floor;").splitlines()
assert all(line.split('\t')[-1] == '1' for line in counts), 'Unexpected cabinet count per floor'
print(f'PASS: {len(counts)} floors, one corridor cabinet each; only unused, unconfigured extra cabinets removed.')
