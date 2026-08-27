from apps.companies.models import Company
qs = Company.objects.filter(profile_url__contains='example.invalid')
print('TO_DELETE', qs.count())
qs.delete()
print('DELETED')
