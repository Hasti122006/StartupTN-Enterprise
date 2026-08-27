from apps.companies.models import Company
obj, created = Company.objects.get_or_create(company_name='PIPE-TEST', profile_url='https://example.invalid/pipe-test-98765', defaults={'founders':'','sector':'','current_stage':''})
print('CREATED' if created else 'EXISTS', getattr(obj,'id',None))
cnt = Company.objects.filter(company_name='PIPE-TEST').count()
print('COUNT:',cnt)
if created:
    obj.delete()
    print('DELETED')
