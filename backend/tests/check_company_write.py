from apps.companies.models import Company
from django.db import IntegrityError

profile = 'https://example.invalid/test-verify-12345'
try:
    obj, created = Company.objects.get_or_create(
        company_name='TEST-VERIFY',
        profile_url=profile,
        defaults={
            'founders': '',
            'sector': '',
            'current_stage': '',
        }
    )
    print('CREATED' if created else 'EXISTS', obj.id)
    cnt = Company.objects.filter(company_name='TEST-VERIFY').count()
    print('COUNT_AFTER_CREATE:', cnt)
    if created:
        obj.delete()
        print('DELETED')
except Exception as e:
    import traceback; traceback.print_exc()
    print('ERROR', e)
