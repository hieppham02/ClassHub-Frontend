import sys
sys.path.insert(0, '.codex-temp/db-english')
from db import run

if '--apply' not in sys.argv:
    print(run("SELECT r.building_id,r.floor,r.id,r.name,c.id FROM room r LEFT JOIN cabinet c ON c.room_id=r.id WHERE r.location_type='ROOM' ORDER BY r.building_id,r.floor,r.id;"))
