from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("companies", "0002_company_authenticated_profile_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="profile_url",
            field=models.URLField(max_length=255, unique=True),
        ),
    ]
