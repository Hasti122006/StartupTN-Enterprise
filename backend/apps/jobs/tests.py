from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.jobs.models import Job

User = get_user_model()


class JobsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='operator@startuptn.com',
            password='Operator@123456',
            full_name='Operator User',
            role='operator'
        )
        self.job = Job.objects.create(
            status='completed',
            start_page=1,
            end_page=5,
            workers=2,
            scraped_companies=100
        )

        login_res = self.client.post('/auth/login', {
            'email': 'operator@startuptn.com',
            'password': 'Operator@123456'
        })
        self.token = login_res.data['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_list_jobs(self):
        response = self.client.get('/jobs')
        self.assertEqual(response.status_code, 200)

    def test_jobs_summary(self):
        response = self.client.get('/jobs/stats/summary')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_companies', response.data)
