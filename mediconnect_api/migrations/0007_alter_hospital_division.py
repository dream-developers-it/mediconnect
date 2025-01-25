# Generated by Django 5.1.5 on 2025-01-24 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediconnect_api', '0006_alter_hospital_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hospital',
            name='division',
            field=models.CharField(choices=[('DHA', 'Dhaka'), ('CTG', 'Chittagong'), ('SYL', 'Sylhet'), ('RAJ', 'Rajshahi'), ('KHU', 'Khulna'), ('BAR', 'Barisal'), ('RAN', 'Rangpur'), ('MYM', 'Mymensingh')], max_length=3, null=True),
        ),
    ]