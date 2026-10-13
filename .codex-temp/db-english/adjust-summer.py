import datetime as dt
import hashlib
import json
import random
import sys
import tempfile
from collections import Counter
from pathlib import Path
from db import ROOT, run

sys.stdout.reconfigure(encoding='utf-8')
rng = random.Random(2026101204)

def main():
    result_file = ROOT / 'summer-adjustment-result.json'
    assert not result_file.exists(), 'Adjustment already applied; stopped to avoid reducing data twice.'
    columns = run("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='borrowing_session' ORDER BY ORDINAL_POSITION;").splitlines()
    snapshot_sql = 'SELECT id,JSON_OBJECT(' + ','.join("'" + c + "',`" + c + '`' for c in columns) + ') FROM borrowing_session ORDER BY id;'
    snapshots = {int(line.split('\t', 1)[0]): line.split('\t', 1)[1] for line in run(snapshot_sql).splitlines()}
    before = run("SELECT DATE_FORMAT(borrowing_date,'%Y-%m'),COUNT(*) FROM borrowing_session GROUP BY 1 ORDER BY 1;")
    summer = []
    for line in run("SELECT id,DATE_FORMAT(borrowing_date,'%Y-%m'),room_id,slot_id,status FROM borrowing_session WHERE MONTH(borrowing_date) IN (6,7) ORDER BY id;").splitlines():
        sid, month, room, slot, status = line.split('\t')
        assert int(sid) > 32 and status in ('COMPLETED', 'CANCELED'), 'Unexpected original/open summer session; stopped.'
        summer.append({'id': int(sid), 'month': month, 'room': room, 'slot': int(slot), 'status': status})
    assert summer
    # Restrict changes to the dates in the earlier generated history plan.
    period = json.loads((ROOT / 'session-plan.json').read_text(encoding='utf-8'))
    summer_ids = set(row['id'] for row in summer)
    safe = int(run("SELECT COUNT(*) FROM borrowing_session WHERE MONTH(borrowing_date) IN (6,7) AND borrowing_date BETWEEN '" + period['start'] + "' AND '" + period['end'] + "';").strip())
    assert safe == len(summer)
    keep = set()
    monthly = []
    for month in sorted({row['month'] for row in summer}):
        rows = [row for row in summer if row['month'] == month]
        rate = 0.12 if month.endswith('-06') else 0.18
        target = round(len(rows) * rate)
        rooms = [room for room, _ in Counter(row['room'] for row in rows).most_common(3)]
        eligible = [row for row in rows if row['room'] in rooms and row['slot'] <= 4]
        assert len(eligible) >= target
        # Keep a few summer classrooms, with variation across dates and slots.
        selected = rng.sample(eligible, target)
        keep.update(row['id'] for row in selected)
        monthly.append({'month': month, 'before': len(rows), 'after': target, 'reduction_percent': round((1-target/len(rows))*100, 1), 'rooms': rooms})
    remove = sorted(summer_ids - keep)
    summary = {'months': monthly, 'remove_count': len(remove), 'total_before': len(snapshots), 'total_after': len(snapshots)-len(remove)}
    print(json.dumps(summary))
    if '--apply' not in sys.argv:
        return
    backup = Path(tempfile.mkdtemp(prefix='classhub-summer-')) / 'before.sql'
    backup.write_text(run(dump=True), encoding='utf-8')
    (ROOT / 'summer-backup-path.txt').write_text(str(backup), encoding='utf-8')
    sql = '''CREATE TEMPORARY TABLE summer_check (ok INT CHECK(ok=1));
        START TRANSACTION;
        DELETE FROM borrowing_session WHERE id IN (''' + ','.join(map(str, remove)) + ''') AND id>32 AND status IN ('COMPLETED','CANCELED') AND MONTH(borrowing_date) IN (6,7);
        INSERT INTO summer_check VALUES (ROW_COUNT()=''' + str(len(remove)) + ''');
        COMMIT;'''
    run(sql)
    after = {int(line.split('\t', 1)[0]): line.split('\t', 1)[1] for line in run(snapshot_sql).splitlines()}
    expected = {sid: value for sid, value in snapshots.items() if sid not in set(remove)}
    assert after == expected, 'Surviving records changed.'
    assert int(run('SELECT COUNT(DISTINCT borrower_id) FROM borrowing_session;')) == 46
    summary.update(backup=str(backup), removed_ids=remove, unchanged_remaining_records=True, monthly_after=run("SELECT DATE_FORMAT(borrowing_date,'%Y-%m'),COUNT(*) FROM borrowing_session GROUP BY 1 ORDER BY 1;").splitlines())
    result_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in summary.items() if key != 'removed_ids'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
