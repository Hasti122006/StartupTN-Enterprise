from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("scraper", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"), ("queued", "Queued"), ("running", "Running"),
                    ("paused", "Paused"), ("completed", "Completed"), ("failed", "Failed"),
                    ("stopped", "Stopped"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
            ),
        ),
    ]
