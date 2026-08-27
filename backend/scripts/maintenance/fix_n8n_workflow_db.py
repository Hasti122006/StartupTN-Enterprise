import sqlite3
import json

DB_PATH = r'd:\company project\tnstartup\n8n_workflow.sqlite'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("select id, name, active from workflow_entity order by name")
rows = cur.fetchall()
for wid, name, active in rows:
    print('WORKFLOW', wid, name, 'active=', bool(active))

cur.execute("select id, name, active, nodes from workflow_entity where active = 0")
rows = cur.fetchall()
for wid, name, active, nodes_json in rows:
    print('INACTIVE DUPLICATE WORKFLOW TO RETIRE:', wid, name)
    cur.execute("delete from webhook_entity where workflowId = ?", (wid,))
    print('REMOVED WEBHOOK_ENTITY FOR OLD COPY:', wid)

conn.commit()
conn.close()
print('FIXED_N8N_WORKFLOW_DB')
