import sqlite3
import json

conn = sqlite3.connect('backend/metrics_helpdesk.db')
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS raw_tickets")
cursor.execute('''
CREATE TABLE raw_tickets (
    tid TEXT PRIMARY KEY,
    st TEXT,
    pri TEXT,
    src TEXT,
    typ TEXT,
    ag TEXT,
    grp TEXT,
    lob TEXT,
    rt TEXT,
    ct TEXT,
    hrs REAL,
    cr TEXT,
    rv TEXT,
    cd TEXT,
    mo TEXT,
    wk TEXT,
    ph TEXT
)
''')

cursor.execute("DROP TABLE IF EXISTS raw_calls")
cursor.execute('''
CREATE TABLE raw_calls (
    cid TEXT PRIMARY KEY,
    ct TEXT,
    camp TEXT,
    cno TEXT,
    cd_old TEXT,
    st TEXT,
    ag TEXT,
    dis TEXT,
    sts TEXT,
    cd TEXT,
    mo TEXT,
    ph TEXT
)
''')

print("Loading raw_hd.json...")
with open('backend/raw_hd.json', 'r', encoding='utf-8') as f:
    hd_data = json.load(f)

print("Inserting tickets...")
for row in hd_data:
    cursor.execute('''
    INSERT OR REPLACE INTO raw_tickets (tid, st, pri, src, typ, ag, grp, lob, rt, ct, hrs, cr, rv, cd, mo, wk, ph)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row.get('tid'), row.get('st'), row.get('pri'), row.get('src'), row.get('typ'), row.get('ag'), row.get('grp'), row.get('lob'), row.get('rt'), row.get('ct'), row.get('hrs'), row.get('cr'), row.get('rv'), row.get('cd'), row.get('mo'), row.get('wk'), row.get('ph')))

print("Loading raw_hda.json...")
with open('backend/raw_hda.json', 'r', encoding='utf-8') as f:
    hda_data = json.load(f)

print("Inserting calls...")
for row in hda_data:
    cursor.execute('''
    INSERT OR REPLACE INTO raw_calls (cid, ct, camp, cno, cd_old, st, ag, dis, sts, cd, mo, ph)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row.get('cid'), row.get('ct'), row.get('camp'), row.get('cno'), row.get('cd_old'), row.get('st'), row.get('ag'), row.get('dis'), row.get('sts'), row.get('cd'), row.get('mo'), row.get('ph')))

conn.commit()
conn.close()
print("Done inserting raw data into DB.")
