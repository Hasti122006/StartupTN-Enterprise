#!/usr/bin/env python3
import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND_ROOT = os.path.join(ROOT, 'backend')
if os.path.isdir(BACKEND_ROOT):
    sys.path.insert(0, BACKEND_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from apps.core.redis import ACTIVE_JOB_KEY, get_redis_client
from apps.scraper.models import Job


def parse_args():
    parser = argparse.ArgumentParser(description='Reset a stale active scraper job without touching unrelated records.')
    parser.add_argument('--job-id', type=int, required=True, help='Job ID to reset')
    parser.add_argument('--apply', action='store_true', help='Apply the reset instead of only previewing it')
    return parser.parse_args()


def main():
    args = parse_args()
    redis_client = get_redis_client()
    active_job = redis_client.get(ACTIVE_JOB_KEY)
    job = Job.objects.filter(id=args.job_id).first()

    print(f'Job lookup: {args.job_id}')
    if job is None:
        print('Result: no matching Job row found; nothing to change.')
        return 0

    print(f'Current job row: id={job.id} status={job.status} start_page={job.start_page} end_page={job.end_page} test_mode={job.test_mode} company_limit={job.company_limit}')
    print(f'Current Redis active_job_id: {active_job}')

    if job.status not in {'queued', 'running', 'paused'}:
        print(f'Preview only: Job {args.job_id} is already in a non-active state ({job.status}), so no reset is needed.')
        return 0

    change_summary = [
        f'Update Job #{job.id} status from {job.status} to failed',
        'Set error_message to "Reset stale queued active job before controlled validation."',
        'Clear the Redis key scraper:active_job_id',
    ]
    print('Would change:')
    for item in change_summary:
        print(f'  - {item}')

    if not args.apply:
        print('Dry run only; no database or Redis changes were made.')
        return 0

    job.status = 'failed'
    job.error_message = 'Reset stale active job before controlled validation.'
    job.message = 'Reset stale active job before controlled validation.'
    job.save(update_fields=['status', 'error_message', 'message', 'updated_at'])
    redis_client.delete(ACTIVE_JOB_KEY)

    print('Applied reset successfully.')
    print(f'Updated: Job #{job.id} status={job.status}')
    print(f'Redis active_job_id after reset: {redis_client.get(ACTIVE_JOB_KEY)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
