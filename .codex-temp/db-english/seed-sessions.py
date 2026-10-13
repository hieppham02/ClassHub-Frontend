import datetime as dt, random, json, tempfile, hashlib
from pathlib import Path
from db import run, ROOT

today=dt.date(2026,10,12)
start=dt.date(2026,4,12)
end=today-dt.timedelta(days=1)
rng=random.Random(20261012)
fields=['borrower_id','room_id','borrowing_date','slot_id','status','created_at','otp','otp_expires_at','received_at','returned_at','returner_id','delegate_id','is_cabinet_open','return_condition','return_note','cancellation_reason']
def q(value):
    if value is None:return 'NULL'
    if isinstance(value,int):return str(value)
    return "'"+str(value).replace('\\','\\\\').replace("'","''")+"'"
slots=[]
for line in run('SELECT id,start_time,end_time FROM class_slot ORDER BY id;').splitlines():
    sid,a,b=line.split('\t');slots.append((int(sid),dt.time.fromisoformat(a),dt.time.fromisoformat(b)))
assert [s[0] for s in slots]==[1,2,3,4,5]
accounts=run("SELECT id FROM account WHERE is_active=1 AND role IN ('SINHVIEN','GIANGVIEN') ORDER BY id;").splitlines()
assert len(accounts)>=4
rooms=[]
for line in run("SELECT r.id,r.building_id FROM room r WHERE r.status='HOAT_DONG' AND EXISTS(SELECT 1 FROM cabinet c WHERE c.room_id=r.id) ORDER BY r.id;").splitlines():
    room,building=line.split('\t');rooms.append((room,building))
assert len(rooms)>=4
existing=run('SELECT id,borrower_id,room_id,borrowing_date,slot_id,status FROM borrowing_session ORDER BY id;').splitlines()
before_count=int(run('SELECT COUNT(*) FROM borrowing_session;'))
occupied=set();occupied_accounts=set()
for line in existing:
    sid,account,room,date,slot,status=line.split('\t')
    occupied.add((room,date,int(slot)))
    occupied_accounts.add((account,date,int(slot)))
cancel_count=int(run("SELECT COUNT(*) FROM borrowing_session WHERE status='CANCELED';"))
cancel_rate=cancel_count/max(1,before_count)
rows=[];date=start
while date<=end:
    date_s=date.isoformat();busy={}
    for sid,begin,finish in slots:
        if date.weekday()==6:
            count=rng.randint(1,2) if sid in (2,3) and rng.random()<.12 else 0
        elif sid==5:
            count=rng.randint(1,3) if rng.random()<.35 else 0
        else:
            count=max(1,{1:5,2:6,3:5,4:4}[sid] + rng.choice([-1,0,0,1])-(1 if date.weekday()==5 else 0))
        begin_dt=dt.datetime.combine(date,begin)
        finish_dt=dt.datetime.combine(date,finish)+(dt.timedelta(days=1) if finish<begin else dt.timedelta())
        available_accounts=[a for a in accounts if (a,date_s,sid) not in occupied_accounts and busy.get(a,dt.datetime.min)<=begin_dt]
        available_rooms=[r for r in rooms if (r[0],date_s,sid) not in occupied]
        rng.shuffle(available_accounts)
        # Stable weekday/slot preferences plus variation, not identical room usage.
        preferred=['DTD','EAUT','PLC','TT','VNB'][(date.weekday()+sid)%5]
        available_rooms.sort(key=lambda r:rng.random()+(0.8 if r[1]==preferred else 0),reverse=True)
        for account,(room,building) in zip(available_accounts[:count],available_rooms[:count]):
            canceled=rng.random()<cancel_rate
            received=begin_dt+dt.timedelta(minutes=rng.randint(0,8))
            created=begin_dt-dt.timedelta(minutes=rng.randint(10,120))
            returned=finish_dt+dt.timedelta(minutes=rng.randint(16,35) if rng.random()<.1 else rng.randint(-10,10))
            assert created<received<returned and returned.date()<=end
            status='CANCELED' if canceled else 'COMPLETED'
            rows.append([account,room,date_s,sid,status,created,None,None,
                None if canceled else received,None if canceled else returned,
                None if canceled else account,None,0,'BINH_THUONG',None,None])
            occupied.add((room,date_s,sid));occupied_accounts.add((account,date_s,sid))
            if not canceled:busy[account]=returned
    date+=dt.timedelta(days=1)
assert rows
assert len({(r[1],r[2],r[3]) for r in rows})==len(rows)
plan=ROOT/'session-plan.json'
plan.write_text(json.dumps({'start':str(start),'end':str(end),'before_count':before_count,'rows':[[str(v) if isinstance(v,dt.datetime) else v for v in row] for row in rows]},ensure_ascii=False),encoding='utf-8')
backup_dir=Path(tempfile.gettempdir())/('classhub-sessions-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup_dir.mkdir()
backup=backup_dir/'classhub_db-before.sql'
backup.write_text(run(dump=True),encoding='utf-8')
(ROOT/'session-backup-path.txt').write_text(str(backup),encoding='utf-8')
sql=['SET SESSION time_zone = \'+07:00\';','START TRANSACTION;',
    'CREATE TEMPORARY TABLE session_seed_plan LIKE borrowing_session;']
for batch in range(0,len(rows),250):
    sql.append('INSERT INTO session_seed_plan ('+','.join('`'+f+'`' for f in fields)+') VALUES\n'+',\n'.join('('+','.join(q(v) for v in row)+')' for row in rows[batch:batch+250])+';')
sql.append('INSERT INTO borrowing_session ('+','.join('`'+f+'`' for f in fields)+') SELECT '+','.join('s.`'+f+'`' for f in fields)+' FROM session_seed_plan s WHERE NOT EXISTS (SELECT 1 FROM borrowing_session b WHERE b.room_id=s.room_id AND b.borrowing_date=s.borrowing_date AND b.slot_id=s.slot_id) AND NOT EXISTS (SELECT 1 FROM borrowing_session b WHERE b.borrower_id=s.borrower_id AND b.borrowing_date=s.borrowing_date AND b.slot_id=s.slot_id) ORDER BY s.borrowing_date,s.slot_id,s.room_id;')
sql += ['SELECT ROW_COUNT();','COMMIT;']
(ROOT/'insert-sessions.sql').write_text('\n'.join(sql),encoding='utf-8')
inserted=int(run('\n'.join(sql)).strip())
after_count=int(run('SELECT COUNT(*) FROM borrowing_session;'))
assert after_count-before_count==inserted
assert run('SELECT id,borrower_id,room_id,borrowing_date,slot_id,status FROM borrowing_session WHERE id <= '+str(max(int(s.split('\t')[0]) for s in existing))+' ORDER BY id;').splitlines()==existing
first_id=int(run('SELECT MIN(id) FROM borrowing_session WHERE id > '+str(max(int(s.split('\t')[0]) for s in existing))+';'))
last_id=int(run('SELECT MAX(id) FROM borrowing_session;'))
bad=run(f"SELECT COUNT(*) FROM borrowing_session WHERE id BETWEEN {first_id} AND {last_id} AND status='COMPLETED' AND (received_at IS NULL OR returned_at IS NULL OR received_at >= returned_at OR created_at > received_at);").strip()
assert bad=='0'
duplicates=run(f'SELECT COUNT(*) FROM (SELECT room_id,borrowing_date,slot_id FROM borrowing_session GROUP BY room_id,borrowing_date,slot_id HAVING COUNT(*)>1 AND MAX(id)>={first_id}) t;').strip()
assert duplicates=='0'
(ROOT/'session-result.json').write_text(json.dumps({'inserted':inserted,'first_id':first_id,'last_id':last_id,'total':after_count,'backup':str(backup)}),encoding='utf-8')
print(f'Inserted {inserted} sessions; IDs {first_id}–{last_id}; total {after_count}. Existing records unchanged.')
print(run('SELECT DATE_FORMAT(borrowing_date,\'%Y-%m\'),COUNT(*) FROM borrowing_session GROUP BY 1 ORDER BY 1; SELECT slot_id,COUNT(*) FROM borrowing_session GROUP BY slot_id ORDER BY slot_id;'))
