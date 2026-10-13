import json, uuid
from pathlib import Path
from db import run, ROOT

rooms=run('SELECT id FROM room ORDER BY id LIMIT 10;').splitlines()
assert len(rooms)==10, 'Need ten existing rooms'
def quote(value): return "'"+value.replace("'","''")+"'"
sql=['-- Ten mock nodes; one telemetry message with four readings per node.',
     '-- Airquality is a synthetic index, not CO2, PM2.5 or a standardized AQI.',
     'START TRANSACTION;', 'SET @seed_time = UTC_TIMESTAMP(3);']
codes=[]
for i,room in enumerate(rooms):
    code=f'ROOM-{room}-MOCK-01'; codes.append(code)
    boot=str(uuid.uuid5(uuid.NAMESPACE_URL,'classhub/mock/initial/'+code))
    readings=[
        {'sensorKey':'CURRENT-01','metric':'current','value':round(.3+i*.2,2),'unit':'A','quality':'GOOD'},
        {'sensorKey':'TEMP-01','metric':'temperature','value':round(26+i*.4,1),'unit':'C','quality':'GOOD'},
        {'sensorKey':'HUMIDITY-01','metric':'humidity','value':55+i,'unit':'%','quality':'GOOD'},
        {'sensorKey':'AIR-01','metric':'airquality','value':35+i*3,'unit':'index','quality':'GOOD'}]
    sql.append(f"INSERT INTO iot_node (node_code,room_id,name,data_source,status,last_seen_at,publish_interval_seconds) SELECT {quote(code)}, {quote(room)}, {quote('Mock room node '+room)}, 'MOCK','OFFLINE',NULL,30 WHERE NOT EXISTS (SELECT 1 FROM iot_node WHERE node_code={quote(code)});")
    sql.append(f"INSERT INTO iot_sensor (node_id,boot_id,sequence,measured_at,received_at,clock_synced,data_source,readings_json) SELECT id,{quote(boot)},1,@seed_time,@seed_time,1,'MOCK',{quote(json.dumps(readings,separators=(',',':')))} FROM iot_node n WHERE n.node_code={quote(code)} AND n.data_source='MOCK' AND NOT EXISTS (SELECT 1 FROM iot_sensor s WHERE s.node_id=n.id AND s.boot_id={quote(boot)} AND s.sequence=1);")
sql.append('COMMIT;')
path=ROOT.parents[1]/'docs/database/seed-mock-nodes.sql'
path.write_text('\n'.join(sql)+'\n',encoding='utf-8')
run(path.read_text(encoding='utf-8'))
rows=run("SELECT n.node_code,n.room_id,n.data_source,n.status,s.readings_json FROM iot_node n JOIN iot_sensor s ON s.node_id=n.id WHERE n.node_code IN ("+','.join(quote(c) for c in codes)+") AND s.sequence=1;").splitlines()
assert len(rows)==10,'Unexpected seed row count'
for row in rows:
    code,room,source,status,payload=row.split('\t',4)
    data=json.loads(payload)
    assert source=='MOCK' and len(data)==4
    assert {r['metric'] for r in data}=={'current','temperature','humidity','airquality'}
    print(code,room,'4 mock readings',status)
print('Verified: ten nodes, ten telemetry records, forty readings. No existing business data changed.')
