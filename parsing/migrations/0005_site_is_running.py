# Generated by Django 3.0.2 on 2020-02-01 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0004_auto_20200120_1744'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='is_running',
            field=models.BooleanField(default=False),
        ),
    ]
