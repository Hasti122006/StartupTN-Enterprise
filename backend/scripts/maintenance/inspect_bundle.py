import re
import requests

url = 'https://startuptn.in/static/js/main.e82c2ead.js'
r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
print('STATUS', r.status_code)
text = r.text
patterns = [
    r'https://[^\"\']+',
    r'/ecosystem[^\"\']*',
    r'/api[^\"\']*',
    r'pageNumber',
    r'listSize',
    r'company',
    r'startup',
]
for pattern in patterns:
    matches = re.findall(pattern, text)
    if matches:
        print('PATTERN', pattern)
        seen = []
        for match in matches:
            if match not in seen:
                seen.append(match)
                if len(seen) >= 80:
                    break
        for match in seen:
            print(match)
        print('---')
