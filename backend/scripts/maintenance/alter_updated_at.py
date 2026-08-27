import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
django.setup()
from django.db import connection
with connection.cursor() as c:
    c.execute("ALTER TABLE companies MODIFY COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
print('ALTER OK')
