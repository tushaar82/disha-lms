# Generated migration for SystemConfiguration model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0003_rename_notificatio_user_id_is_read_created_idx_notificatio_user_id_c4e471_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, help_text='Configuration key name', max_length=100, unique=True)),
                ('value', models.TextField(help_text='Configuration value (encrypted if is_encrypted=True)')),
                ('description', models.TextField(blank=True, help_text='Human-readable description of this configuration')),
                ('is_encrypted', models.BooleanField(default=False, help_text='Whether the value is encrypted')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modified_configs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'System Configuration',
                'verbose_name_plural': 'System Configurations',
                'db_table': 'system_configurations',
                'ordering': ['key'],
            },
        ),
        migrations.AddIndex(
            model_name='systemconfiguration',
            index=models.Index(fields=['key'], name='system_conf_key_idx'),
        ),
    ]
