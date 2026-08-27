import os
import django
import sys

# Ensure backend folder is on sys.path so imports like 'apps.companies' resolve
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

script_path = os.path.join(BASE, 'check_company_write.py')
with open(script_path, 'r', encoding='utf-8') as f:
    code = f.read()

exec(compile(code, script_path, 'exec'))
