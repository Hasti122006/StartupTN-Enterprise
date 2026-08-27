import sqlite3
import json

conn = sqlite3.connect(r'D:\company project\tnstartup\n8n-live.sqlite')
cur = conn.cursor()
cur.execute('SELECT id, name, active, versionId, createdAt, updatedAt, nodes FROM workflow_entity ORDER BY updatedAt DESC')
for wf_id, name, active, versionId, createdAt, updatedAt, nodes_text in cur.fetchall():
    try:
        nodes = json.loads(nodes_text or '[]')
    except Exception:
        nodes = []
    print('WF', wf_id, 'active=', bool(active), 'updatedAt=', updatedAt, 'version=', versionId)
    for node in nodes:
        if node.get('name') == 'Trigger Django Scraper Worker API':
            params = node.get('parameters') or {}
            print('worker node:', json.dumps(params, indent=2))
        if node.get('name') == 'Webhook Start Scraper':
            params = node.get('parameters') or {}
            print('webhook node:', json.dumps(params, indent=2))
    print('---')
conn.close()
