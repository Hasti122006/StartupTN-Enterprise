from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("companies", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="company",
            name="ecosystem_category",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="company",
            name="team_members",
            field=models.TextField(blank=True, null=True),
        ),
    ]
