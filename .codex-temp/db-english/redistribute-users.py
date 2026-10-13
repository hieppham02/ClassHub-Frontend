import csv
import datetime as dt
import json
import random
import sys
import tempfile
from collections import Counter
from pathlib import Path
from db import ROOT, run

sys.stdout.reconfigure(encoding='utf-8')
rng = random.Random(2026101203)

def q(value):
    if value is None or value == 'NULL':
        return 'NULL'
    return "'" + str(value).replace('\\', '\\\\').replace("'", "''") + "'"

def main():
    manifest = list(csv.DictReader((ROOT / 'created-users.csv').open(encoding='utf-8-sig')))
    users = [a['id'] for a in manifest]
    assert len(users) == 46 and len(set(users)) == 46
    valid = run('SELECT id FROM account WHERE is_active=1 AND role IN (\'SINHVIEN\',\'GIANGVIEN\') AND id IN (' + ','.join(map(q, users)) + ') ORDER BY id;').splitlines()
    assert set(valid) == set(users)
    columns = run("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='borrowing_session' ORDER BY ORDINAL_POSITION;").splitlines()
    immutable = [c for c in columns if c not in ('borrower_id', 'returner_id', 'delegate_id')]
    snapshot_sql = 'SELECT JSON_OBJECT(' + ','.join(q(c) + ',`' + c + '`' for c in immutable) + ') FROM borrowing_session ORDER BY id;'
    before = run(snapshot_sql)
    slots = {int(row.split('\t')[0]): dt.time.fromisoformat(row.split('\t')[1]) for row in run('SELECT id,start_time FROM class_slot;').splitlines()}
    rows = []
    missing_received = 0
    for line in run('SELECT id,borrower_id,returner_id,delegate_id,status,borrowing_date,slot_id,received_at,returned_at,created_at FROM borrowing_session ORDER BY borrowing_date,slot_id,id;').splitlines():
        sid, borrower, returner, delegate, status, date, slot, received, returned, created = line.split('\t')
        assert status in ('COMPLETED', 'CANCELED'), 'Open sessions found; stopped before changing ownership.'
        assert (status == 'COMPLETED') == (returned != 'NULL')
        start = dt.datetime.fromisoformat(received) if received != 'NULL' else dt.datetime.combine(dt.date.fromisoformat(date), slots[int(slot)])
        if status == 'COMPLETED' and received == 'NULL':
            missing_received += 1
            start = dt.datetime.fromisoformat(created)
        end = dt.datetime.fromisoformat(returned) if returned != 'NULL' else start
        assert end >= start
        rows.append(dict(id=int(sid), old_borrower=borrower, old_returner=returner, old_delegate=delegate, status=status, date=date, slot=int(slot), start=start, end=end))
    rows.sort(key=lambda r: (r['start'], r['id']))
    busy_until = {}
    occupied_slots = set()
    borrower_counts = Counter()
    delegation_counts = Counter()
    assignments = []
    for row in rows:
        candidates = [u for u in users if (u, row['date'], row['slot']) not in occupied_slots and busy_until.get(u, dt.datetime.min) <= row['start']]
        assert candidates, 'Insufficient users without time overlaps.'
        # Random choice, with gentle balancing so every account has history.
        rng.shuffle(candidates)
        borrower = min(candidates, key=lambda u: borrower_counts[u] + rng.uniform(0, 8))
        borrower_counts[borrower] += 1
        occupied_slots.add((borrower, row['date'], row['slot']))
        if row['status'] == 'COMPLETED':
            busy_until[borrower] = row['end']
        delegate = None
        returner = borrower if row['status'] == 'COMPLETED' else None
        if row['status'] == 'COMPLETED' and (row['old_delegate'] != 'NULL' or rng.random() < 0.30):
            candidates = [u for u in candidates if u != borrower]
            assert candidates
            rng.shuffle(candidates)
            delegate = min(candidates, key=lambda u: delegation_counts[u] + rng.uniform(0, 5))
            delegation_counts[delegate] += 1
            occupied_slots.add((delegate, row['date'], row['slot']))
            busy_until[delegate] = row['end']
            if rng.random() < 0.75:
                returner = delegate
        assignments.append({**row, 'borrower_id': borrower, 'returner_id': returner, 'delegate_id': delegate})
    assert set(borrower_counts) == set(users)
    assert set(delegation_counts) == set(users)
    summary = {'sessions': len(rows), 'borrowers': len(borrower_counts), 'delegated_sessions': sum(a['delegate_id'] is not None for a in assignments), 'returned_by_delegate': sum(a['delegate_id'] is not None and a['delegate_id'] == a['returner_id'] for a in assignments), 'borrow_count_min': min(borrower_counts.values()), 'borrow_count_max': max(borrower_counts.values())}
    summary['legacy_missing_received_at'] = missing_received
    print(json.dumps(summary))
    if '--apply' not in sys.argv:
        return
    report = ROOT / 'redistributed-sessions.csv'
    assert not report.exists(), 'Existing update report found; stopped to avoid repeating the update.'
    backup = Path(tempfile.mkdtemp(prefix='classhub-user-history-')) / 'before.sql'
    backup.write_text(run(dump=True), encoding='utf-8')
    (ROOT / 'redistribution-backup-path.txt').write_text(str(backup), encoding='utf-8')
    values = ['(' + ','.join([str(a['id'])] + [q(a[k]) for k in ['old_borrower', 'old_returner', 'old_delegate', 'borrower_id', 'returner_id', 'delegate_id']]) + ')' for a in assignments]
    sql = '''CREATE TEMPORARY TABLE reassignment_plan (
        id INT PRIMARY KEY, old_borrower VARCHAR(50), old_returner VARCHAR(50), old_delegate VARCHAR(50),
        borrower_id VARCHAR(50), returner_id VARCHAR(50), delegate_id VARCHAR(50)) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        CREATE TEMPORARY TABLE reassignment_check (ok INT CHECK (ok=1));
        INSERT INTO reassignment_plan VALUES ''' + ','.join(values) + ''';
        START TRANSACTION;
        UPDATE borrowing_session b JOIN reassignment_plan p ON p.id=b.id
        SET b.borrower_id=p.borrower_id, b.returner_id=p.returner_id, b.delegate_id=p.delegate_id
        WHERE b.borrower_id <=> p.old_borrower AND b.returner_id <=> p.old_returner
        AND b.delegate_id <=> p.old_delegate AND b.status IN ('COMPLETED','CANCELED');
        INSERT INTO reassignment_check VALUES (ROW_COUNT()=''' + str(len(assignments)) + ''');
        INSERT INTO reassignment_check
        SELECT COUNT(*)=''' + str(len(assignments)) + ''' FROM borrowing_session b JOIN reassignment_plan p ON p.id=b.id
        WHERE b.borrower_id=p.borrower_id AND b.returner_id <=> p.returner_id AND b.delegate_id <=> p.delegate_id;
        COMMIT;'''
    run(sql)
    assert run(snapshot_sql) == before, 'Fields outside account assignment changed.'
    actual = run('SELECT id,borrower_id,returner_id,delegate_id FROM borrowing_session ORDER BY id;')
    expected = {a['id']: a for a in assignments}
    for line in actual.splitlines():
        sid, borrower, returner, delegate = line.split('\t')
        a = expected[int(sid)]
        assert (borrower, returner, delegate) == tuple(a[k] or 'NULL' for k in ['borrower_id', 'returner_id', 'delegate_id'])
        assert delegate == 'NULL' or delegate != borrower
        assert returner == 'NULL' or returner in (borrower, delegate)
    # Verify actual received/returned intervals and date/slot uniqueness for all participants.
    intervals = {u: [] for u in users}
    used = set()
    for a in assignments:
        for u in [a['borrower_id']] + ([a['delegate_id']] if a['delegate_id'] else []):
            key = (u, a['date'], a['slot'])
            assert key not in used
            used.add(key)
            if a['status'] == 'COMPLETED': intervals[u].append((a['start'], a['end']))
    for entries in intervals.values():
        entries.sort()
        assert all(left[1] <= right[0] for left, right in zip(entries, entries[1:]))
    with report.open('w', encoding='utf-8-sig', newline='') as f:
        keys = ['id', 'old_borrower', 'old_returner', 'old_delegate', 'borrower_id', 'returner_id', 'delegate_id']
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(sorted(assignments, key=lambda a: a['id']))
    summary.update(verified=True, backup=str(backup), report=str(report))
    print(json.dumps(summary, ensure_ascii=False))

if __name__ == '__main__':
    main()
