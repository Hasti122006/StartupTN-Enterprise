from django.test import TestCase
from rest_framework.test import APIClient
from apps.companies.models import Company


class CompaniesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            company_name='AgriTech Solutions',
            sector='Agriculture',
            current_stage='Seed',
            location='Chennai',
            profile_url='https://startuptn.in/ecosystem/agritech'
        )


    def test_list_companies(self):
        response = self.client.get('/companies/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)

    def test_company_detail(self):
        response = self.client.get(f'/companies/{self.company.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['company_name'], 'AgriTech Solutions')

    def test_stage_statistics_group_text_stages(self):
        Company.objects.create(
            company_name='Second Stage Company',
            current_stage='Seed',
            profile_url='https://startuptn.in/ecosystem/second-stage',
        )
        response = self.client.get('/companies/stats/stages')
        self.assertEqual(response.status_code, 200)
        self.assertIn({'stage': 'Seed', 'count': 2}, response.data)
