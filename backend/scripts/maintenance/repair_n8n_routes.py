import sqlite3

DB_PATH = r'd:\company project\tnstartup\n8n_db_live.sqlite'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("select workflowId, webhookPath, method, node from webhook_entity order by workflowId")
print('BEFORE', cur.fetchall())
cur.execute("update webhook_entity set webhookPath = 'webhook-export-companies' where workflowId = ? and node = ?", ('LiID8F9ndug1s0vH', 'Webhook Export Data'))
conn.commit()
cur.execute("select workflowId, webhookPath, method, node from webhook_entity order by workflowId")
print('AFTER', cur.fetchall())
conn.close()
