# Generated by Django 3.0.2 on 2020-01-19 12:23

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseURL',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_url', models.URLField()),
                ('parser', models.IntegerField(choices=[('Selenium', 0), ('Requests', 1)])),
                ('identifier_type', models.IntegerField(choices=[('id', 0), ('class', 1), ('xpath', 2), ('tag', 3)])),
                ('identifier', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('price', models.IntegerField(blank=True, null=True)),
                ('photo_path', models.CharField(blank=True, max_length=200, null=True)),
                ('user', models.ManyToManyField(related_name='sites', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
