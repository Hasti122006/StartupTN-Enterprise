import sqlite3

conn = sqlite3.connect(r'D:\company project\tnstartup\n8n-live.sqlite')
cur = conn.cursor()

print('tables:')
for row in cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table') ORDER BY name"):
    print(row)

print('workflow table columns:')
for row in cur.execute('PRAGMA table_info(workflow_entity)'):
    print(row)

print('workflow rows:')
for row in cur.execute('SELECT id, name, active, versionId, createdAt, updatedAt FROM workflow_entity ORDER BY updatedAt DESC'):
    print(row)

print('webhook node ids maybe?')
for row in cur.execute('SELECT id, name, active, versionId, createdAt, updatedAt FROM workflow_entity WHERE active = 1'):
    print(row)

conn.close()
