import sqlite3

source = r'D:\company project\tnstartup\live-n8n-container-db.sqlite'
conn = sqlite3.connect(source)
cur = conn.cursor()
cur.execute("UPDATE workflow_entity SET active = 0 WHERE id = 'LiID8F9ndug1s0vH'")
conn.commit()
rows = cur.execute("SELECT id, name, active, versionId, createdAt, updatedAt FROM workflow_entity ORDER BY updatedAt DESC").fetchall()
print(rows)
conn.close()
