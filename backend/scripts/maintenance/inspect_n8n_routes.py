import sqlite3

DB_PATH = r'd:\company project\tnstartup\n8n_db_live.sqlite'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("select workflowId, webhookPath, method, node from webhook_entity order by workflowId")
print('WEBHOOK_ENTITY_ROWS', cur.fetchall())

cur.execute("select id, name, active from workflow_entity order by name")
rows = cur.fetchall()
print('WORKFLOW_ENTITY_ROWS', rows)

conn.close()
