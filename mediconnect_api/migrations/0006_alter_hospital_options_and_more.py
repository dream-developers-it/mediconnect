# Generated by Django 5.1.5 on 2025-01-24 17:29

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediconnect_api', '0005_userprofile_created_at_userprofile_updated_at_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='hospital',
            options={'ordering': ['name']},
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='contact_number',
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='location',
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='mapurl',
        ),
        migrations.AddField(
            model_name='hospital',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='city',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='hospital',
            name='division',
            field=models.CharField(choices=[('Dhaka', 'Dhaka'), ('Chittagong', 'Chittagong'), ('Rajshahi', 'Rajshahi'), ('Khulna', 'Khulna'), ('Barishal', 'Barishal'), ('Sylhet', 'Sylhet'), ('Rangpur', 'Rangpur'), ('Mymensingh', 'Mymensingh')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='phone',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='hospital',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='hospital',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='hospital',
            name='image',
            field=models.ImageField(default='images/hospital-default.jpg', upload_to='hospital_images/'),
        ),
        migrations.AlterField(
            model_name='hospital',
            name='website',
            field=models.URLField(blank=True, null=True),
        ),
    ]
