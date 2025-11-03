# Generated migration for Notification and Task models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('centers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('notification_type', models.CharField(
                    choices=[('info', 'Information'), ('warning', 'Warning'), ('error', 'Error'), ('success', 'Success')],
                    default='info',
                    max_length=20
                )),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('action_url', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'db_table': 'notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('task_type', models.CharField(
                    choices=[('follow_up', 'Follow Up'), ('approval', 'Approval'), ('review', 'Review'), ('action', 'Action Required')],
                    default='action',
                    max_length=20
                )),
                ('priority', models.CharField(
                    choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
                    db_index=True,
                    default='medium',
                    max_length=20
                )),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
                    db_index=True,
                    default='pending',
                    max_length=20
                )),
                ('due_date', models.DateField(blank=True, db_index=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assigned_tasks',
                    to=settings.AUTH_USER_MODEL
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_tasks',
                    to=settings.AUTH_USER_MODEL
                )),
                ('modified_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='modified_tasks',
                    to=settings.AUTH_USER_MODEL
                )),
                ('related_center', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tasks',
                    to='centers.center'
                )),
            ],
            options={
                'verbose_name': 'Task',
                'verbose_name_plural': 'Tasks',
                'db_table': 'tasks',
                'ordering': ['priority', 'due_date'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read', '-created_at'], name='notificatio_user_id_is_read_created_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['assigned_to', 'status', 'priority'], name='tasks_assigned_status_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['due_date', 'status'], name='tasks_due_date_status_idx'),
        ),
    ]
