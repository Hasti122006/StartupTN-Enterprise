from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("scraper", "0002_alter_job_status")]

    operations = [
        migrations.AddField(model_name="job", name="company_limit", field=models.PositiveSmallIntegerField(default=0, help_text="0 means no profile limit")),
        migrations.AddField(model_name="job", name="test_mode", field=models.BooleanField(default=False)),
    ]
