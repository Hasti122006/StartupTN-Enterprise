import os
import time
import json
import urllib.request

# Dispatch worker start to local backend
url = 'http://localhost:8000/scraper/worker/start'
job_id = 38
headers = {'Content-Type': 'application/json', 'X-API-Key': os.environ.get('N8N_API_KEY', '')}
data = json.dumps({'job_id': job_id}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print('HTTP_STATUS:' + str(resp.status))
        print(resp.read().decode('utf-8'))
except Exception as e:
    print('ERROR:' + str(e))

# Poll job status via Django ORM
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()
from apps.scraper.models import Job

print('\nPolling job status for up to 300 seconds...')
start = time.time()
last = None
while time.time() - start < 300:
    try:
        j = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        print('Job missing')
        break
    s = (j.status, j.progress, j.scraped_companies, j.failed_companies, j.updated_at.isoformat() if j.updated_at else None)
    if s != last:
        print('JOB_STATUS_UPDATE:', s)
        last = s
    if j.status in ('completed', 'failed', 'stopped'):
        print('JOB_TERMINAL:', j.status)
        break
    time.sleep(5)
else:
    print('TIMEOUT_WAITING_FOR_JOB')
