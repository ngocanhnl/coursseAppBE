# Generated by Django 5.2 on 2025-04-19 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_alter_classcategory_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='classcategory',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='courses/%Y/%m/'),
        ),
    ]
