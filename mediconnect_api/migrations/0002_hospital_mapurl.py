# Generated by Django 5.1.5 on 2025-01-23 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediconnect_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='mapurl',
            field=models.TextField(blank=True, help_text='Google Maps embed URL'),
        ),
    ]
