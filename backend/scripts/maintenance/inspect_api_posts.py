import requests

urls = [
    'https://api.startuptn.in/ecosystem/page/get',
    'https://api.startuptn.in/ecosystem/popup/home/list',
    'https://api.startuptn.in/ecosystem/search/engine/home/list',
    'https://api.startuptn.in/ecosystem/hub/list',
    'https://api.startuptn.in/ecosystem/home/services/project/list',
    'https://api.startuptn.in/ecosystem/home/category/list',
    'https://api.startuptn.in/ecosystem/event/home/list',
    'https://api.startuptn.in/ecosystem/home/matrix',
]

payloads = [
    {},
    {'page': 1, 'pageNumber': 1, 'pageSize': 20},
    {'pageNumber': 1, 'pageSize': 20},
    {'type': 'startup'},
    {'type': 'event'},
]

for url in urls:
    print('URL', url)
    for payload in payloads:
        try:
            r = requests.post(url, timeout=30, json=payload, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'})
            print(' POST', payload, '=>', r.status_code, r.text[:1000])
        except Exception as exc:
            print(' POST ERR', payload, exc)
    print('---')
