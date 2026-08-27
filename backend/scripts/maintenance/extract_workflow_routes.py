import sqlite3
import json

DB_PATH = r'd:\company project\tnstartup\n8n_db_live.sqlite'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("select id, name, active, nodes from workflow_entity order by name")
rows = cur.fetchall()
for workflow_id, workflow_name, active, nodes_json in rows:
    print('WORKFLOW_ID', workflow_id)
    print('NAME', workflow_name)
    print('ACTIVE', bool(active))
    try:
        nodes = json.loads(nodes_json or '[]')
    except Exception as exc:
        print('JSON_PARSE_ERROR', exc)
        nodes = []
    for node in nodes:
        name = node.get('name')
        typ = node.get('type')
        params = node.get('parameters') or {}
        if typ == 'n8n-nodes-base.webhook':
            print('WEBHOOK_NODE', name, 'method', params.get('httpMethod'), 'path', params.get('path'))
        elif typ == 'n8n-nodes-base.httpRequest':
            print('HTTP_NODE', name, 'url', params.get('url'))
    print('---')
conn.close()
