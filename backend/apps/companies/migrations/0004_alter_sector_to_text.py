# Generated manually to convert sector CharField to TextField to accept long values
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0003_alter_company_profile_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="sector",
            field=models.TextField(blank=True, null=True),
        ),
    ]
