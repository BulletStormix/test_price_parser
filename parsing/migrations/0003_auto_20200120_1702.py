# Generated by Django 3.0.2 on 2020-01-20 14:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0002_auto_20200119_1539'),
    ]

    operations = [
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.IntegerField()),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.DeleteModel(
            name='BaseURL',
        ),
        migrations.RemoveField(
            model_name='site',
            name='price',
        ),
        migrations.AddField(
            model_name='price',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parsing.Site'),
        ),
    ]