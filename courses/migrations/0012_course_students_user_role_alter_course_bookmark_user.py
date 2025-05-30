# Generated by Django 5.2 on 2025-04-29 04:16

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0011_alter_comment_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='students',
            field=models.ManyToManyField(related_name='enrolled_courses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('admin', 'Admin'), ('tiep_tan', 'Tiếp Tân'), ('hlv', 'Hlv'), ('hoc-vien', 'Hoc Vien')], default='hoc-vien', max_length=20),
        ),
        migrations.AlterField(
            model_name='course',
            name='bookmark_user',
            field=models.ManyToManyField(related_name='bookmark_user', through='courses.Bookmark', to=settings.AUTH_USER_MODEL),
        ),
    ]
