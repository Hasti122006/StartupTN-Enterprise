import requests

urls = [
    'https://startuptn.in/json/startupNavMenu.json',
    'https://startuptn.in/json/enablersNavMenu.json',
    'https://startuptn.in/json/profiledetails.json',
]
for url in urls:
    print('URL', url)
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    print('STATUS', r.status_code)
    print(r.text[:4000])
    print('---')
