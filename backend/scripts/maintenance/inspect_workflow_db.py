import sqlite3
import json

conn = sqlite3.connect(r'd:\company project\tnstartup\n8n_workflow.sqlite')
cur = conn.cursor()
cur.execute("select id, name, active, nodes from workflow_entity order by name")
rows = cur.fetchall()
print('WORKFLOW_ENTITY_ROWS:', len(rows))
for wid, name, active, nodes_json in rows:
    name_normalized = name.strip() if name else name
    print('WORKFLOW:', wid, '|', name_normalized, '| active=', bool(active))
    try:
        nodes = json.loads(nodes_json or '[]') if nodes_json else []
    except Exception as exc:
        print('FAILED_TO_PARSE_NODES_JSON', exc)
        nodes = []
    for n in nodes:
        typ = n.get('type')
        node_name = n.get('name')
        params = n.get('parameters') or {}
        if typ == 'n8n-nodes-base.webhook':
            print('  WEBHOOK node:', node_name, 'method=', params.get('httpMethod'), 'path=', params.get('path'), 'webhookId=', n.get('webhookId'))
        elif typ == 'n8n-nodes-base.httpRequest':
            print('  HTTP_REQUEST node:', node_name, 'method=', params.get('httpMethod'), 'url=', params.get('url'))
    print('---')

cur.execute("select workflowId, webhookPath, method, node, webhookId, pathLength from webhook_entity order by workflowId")
webhooks = cur.fetchall()
print('WEBHOOK_ENTITY_ROWS:', len(webhooks))
for row in webhooks:
    print('WEBHOOK_RECORD:', row)

conn.close()
