import sqlite3

conn = sqlite3.connect(r'D:\company project\tnstartup\n8n-live.sqlite')
cur = conn.cursor()

cur.execute("""SELECT name, type FROM sqlite_master WHERE type IN ('table','index') ORDER BY name""")
print('--- tables/indexes ---')
print(cur.fetchall())

cur.execute("""SELECT id, name, active, versionId, createdAt, updatedAt FROM workflow_entity ORDER BY updatedAt DESC LIMIT 25""")
print('--- workflow_entity rows ---')
for row in cur.fetchall():
    print(row)

cur.execute("""SELECT id, name, active, createdAt, updatedAt, workflowId FROM workflow_entity WHERE name LIKE '%StartupTN%' ORDER BY updatedAt DESC LIMIT 25""")
print('--- matching workflows ---')
for row in cur.fetchall():
    print(row)

conn.close()
