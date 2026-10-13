import csv
import importlib.util
import json
import re
import sys
import subprocess
import tempfile
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from db import run, ROOT

sys.stdout.reconfigure(encoding='utf-8')

SOURCE = Path(r'E:\EAUT\DCCNTT143 Documents\DCCNTT14.3.xlsx')
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def read_students():
    with zipfile.ZipFile(SOURCE) as z:
        strings = [''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        students = []
        for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:sheetData/s:row', NS):
            cells = {}
            for cell in row:
                value = cell.find('s:v', NS)
                if value is not None:
                    cells[re.sub(r'\d+$', '', cell.attrib['r'])] = strings[int(value.text)] if cell.attrib.get('t') == 's' else value.text
            if re.fullmatch(r'2023\d{4}', cells.get('B', '')) and cells.get('C'):
                students.append((cells['B'], cells['C'].strip()))
        assert students and len({s[0] for s in students}) == len(students)
        return students

def quote(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "''") + "'"

def email_name(name):
    plain = ''.join(c for c in unicodedata.normalize('NFD', name.lower().replace('đ', 'd')) if not unicodedata.combining(c))
    words = plain.split()
    return words[-1] + ''.join(w[0] for w in words[:-1]) + '@gmail.com'

def prepare():
    source = read_students()
    old = run('SELECT id,email,full_name,password_hash,role,class_or_department,is_active,created_at FROM account ORDER BY id;')
    existing = [line.split('\t') for line in old.splitlines()]
    ids = {r[0].upper() for r in existing}
    emails = {r[1].lower() for r in existing}
    faculties = [
        ('DCCNTT', 'Khoa công nghệ thông tin'),
        ('DCDDT', 'Khoa điện điện tử'),
        ('DCTCNH', 'Khoa tài chính ngân hàng'),
        ('DCNNA', 'Khoa ngôn ngữ anh'),
    ]
    teacher_count = round(len(source) * 0.1)
    student_count = len(source) - teacher_count
    counts = Counter()
    output = []
    substitutions = []
    for i, (source_id, name) in enumerate(source):
        teacher = i >= student_count
        faculty_index = (i - student_count) % 4 if teacher else i % 4
        prefix, faculty = faculties[faculty_index]
        if teacher:
            account_id = next('GV%04d' % j for j in range(1, 10000) if 'GV%04d' % j not in ids)
            email = email_name(name)
            assert email not in emails, 'Lecturer email collision; no changes applied.'
            unit = faculty
        else:
            account_id = source_id
            if account_id in ids or account_id.lower() + '@eaut.edu.vn' in emails:
                account_id = next('2023%04d' % j for j in range(1, 10000) if '2023%04d' % j not in ids and '2023%04d@eaut.edu.vn' % j not in emails)
                substitutions.append({'source_id': source_id, 'account_id': account_id})
            email = account_id + '@eaut.edu.vn'
            counts[prefix] += 1
            # Spread class numbers over the requested 1..15 range.
            class_number = ((counts[prefix] - 1) * 7) % 15 + 1
            unit = f'{prefix}.14.{class_number}'
        role = 'GIANGVIEN' if teacher else 'SINHVIEN'
        assert len(name) <= 100 and len(unit) <= 50
        output.append({'id': account_id, 'email': email, 'full_name': name, 'role': role, 'class_or_department': unit, 'faculty': faculty})
        ids.add(account_id)
        emails.add(email)
    return output, old, substitutions

def main():
    accounts, old, substitutions = prepare()
    print(json.dumps({'source_count': len(accounts), 'roles': dict(Counter(a['role'] for a in accounts)), 'faculties': [{'faculty': f, 'students': sum(a['faculty'] == f and a['role'] == 'SINHVIEN' for a in accounts), 'lecturers': sum(a['faculty'] == f and a['role'] == 'GIANGVIEN' for a in accounts)} for f in dict.fromkeys(a['faculty'] for a in accounts)], 'id_substitutions': substitutions, 'bcrypt_available': importlib.util.find_spec('bcrypt') is not None}, ensure_ascii=False))
    if '--apply' not in sys.argv:
        return
    def passwords(mode, values):
        result = subprocess.run(['dotnet', str(ROOT.parent / 'user-passwords/bin/Debug/net8.0/user-passwords.dll'), mode], input=json.dumps(values), text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError('BCrypt helper failed.')
        return json.loads(result.stdout)
    report_path = ROOT / 'created-users.csv'
    assert not report_path.exists(), 'Existing insertion report found; stopped to avoid repeat insertion.'
    values = []
    hashes = passwords('hash', ['123456'] * len(accounts))
    assert all(passwords('verify', hashes))
    for a, hashed in zip(accounts, hashes):
        values.append('(' + ','.join(quote(a[k]) for k in ['id', 'email', 'full_name']) + ',' + quote(hashed) + ',' + ','.join(quote(a[k]) for k in ['role', 'class_or_department']) + ',1)')
    backup = Path(tempfile.mkdtemp(prefix='classhub-users-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-')) / 'before.sql'
    backup.write_text(run(dump=True), encoding='utf-8')
    (ROOT / 'users-backup-path.txt').write_text(str(backup), encoding='utf-8')
    sql = 'START TRANSACTION;\nINSERT INTO account (id,email,full_name,password_hash,role,class_or_department,is_active) VALUES\n' + ',\n'.join(values) + ';\nSELECT ROW_COUNT();\nCOMMIT;'
    inserted = run(sql).strip()
    assert inserted == str(len(accounts)), 'Unexpected inserted count: ' + inserted
    original_ids = [line.split('\t')[0] for line in old.splitlines()]
    preserved = run('SELECT id,email,full_name,password_hash,role,class_or_department,is_active,created_at FROM account WHERE id IN (' + ','.join(map(quote, original_ids)) + ') ORDER BY id;')
    assert preserved == old, 'Existing accounts changed.'
    actual = run('SELECT id,email,full_name,password_hash,role,class_or_department,is_active FROM account WHERE id IN (' + ','.join(quote(a['id']) for a in accounts) + ') ORDER BY id;')
    expected = {a['id']: a for a in accounts}
    assert len(actual.splitlines()) == len(accounts)
    stored_hashes = []
    for line in actual.splitlines():
        aid, email, name, hashed, role, unit, active = line.split('\t')
        a = expected[aid]
        assert (email, name, role, unit, active) == (a['email'], a['full_name'], a['role'], a['class_or_department'], '1')
        stored_hashes.append(hashed)
    assert all(passwords('verify', stored_hashes))
    with report_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(accounts[0]))
        writer.writeheader()
        writer.writerows(accounts)
    print(json.dumps({'inserted': len(accounts), 'existing_preserved': len(original_ids), 'all_passwords_verified': True, 'total_accounts': int(run('SELECT COUNT(*) FROM account;').strip()), 'backup': str(backup), 'report': str(report_path)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
