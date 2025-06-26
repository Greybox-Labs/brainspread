# Generated migration for API key models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_user_theme'),
    ]

    operations = [
        migrations.CreateModel(
            name='APIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When this record was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='When this record was last updated')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this record is active (soft delete)')),
                ('deleted_at', models.DateTimeField(blank=True, help_text='When this record was deleted', null=True)),
                ('name', models.CharField(help_text='Human-readable name for this API key', max_length=100, verbose_name='name')),
                ('encrypted_key', models.TextField(blank=True, help_text='Encrypted API key value for retrieval', null=True, verbose_name='encrypted key')),
                ('hashed_key', models.CharField(blank=True, help_text='Hashed API key value for verification only', max_length=128, null=True, verbose_name='hashed key')),
                ('salt', models.CharField(help_text='User-specific salt for key derivation', max_length=44, verbose_name='salt')),
                ('scope', models.CharField(choices=[('read', 'Read Only'), ('write', 'Write Only'), ('read_write', 'Read and Write'), ('admin', 'Administrative')], default='read', help_text='API key permissions scope', max_length=20, verbose_name='scope')),
                ('last_used', models.DateTimeField(blank=True, help_text='Timestamp of last API key usage', null=True, verbose_name='last used')),
                ('expires_at', models.DateTimeField(blank=True, help_text='Optional expiration date for the API key', null=True, verbose_name='expires at')),
                ('created_from_ip', models.GenericIPAddressField(blank=True, help_text='IP address where this key was created', null=True, verbose_name='created from IP')),
                ('last_used_ip', models.GenericIPAddressField(blank=True, help_text='IP address where this key was last used', null=True, verbose_name='last used IP')),
                ('user', models.ForeignKey(help_text='User who owns this API key', on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'api_keys',
                'ordering': ('-created_at',),
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='APIKeyAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When this record was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='When this record was last updated')),
                ('api_key_name', models.CharField(help_text='Name of the API key at time of operation', max_length=100, verbose_name='API key name')),
                ('action', models.CharField(choices=[('created', 'Created'), ('used', 'Used'), ('rotated', 'Rotated'), ('deactivated', 'Deactivated'), ('deleted', 'Deleted'), ('failed_auth', 'Failed Authentication'), ('expired', 'Expired')], help_text='Type of operation performed on the API key', max_length=20, verbose_name='action')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address from which the operation was performed', null=True, verbose_name='IP address')),
                ('user_agent', models.TextField(blank=True, help_text='User agent string from the request', null=True, verbose_name='user agent')),
                ('details', models.JSONField(blank=True, default=dict, help_text='Additional details about the operation', verbose_name='details')),
                ('success', models.BooleanField(default=True, help_text='Whether the operation was successful', verbose_name='success')),
                ('error_message', models.TextField(blank=True, help_text='Error message if operation failed', null=True, verbose_name='error message')),
                ('api_key', models.ForeignKey(blank=True, help_text='API key involved in the operation (null if deleted)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='core.apikey')),
                ('user', models.ForeignKey(help_text='User associated with the API key operation', on_delete=django.db.models.deletion.CASCADE, related_name='api_key_audits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'api_key_audits',
                'ordering': ('-created_at',),
                'default_permissions': (),
            },
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['user', 'is_active'], name='api_keys_user_id_d8ea7a_idx'),
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['expires_at'], name='api_keys_expires_e0e2e1_idx'),
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['last_used'], name='api_keys_last_us_4b5e31_idx'),
        ),
        migrations.AddIndex(
            model_name='apikeyaudit',
            index=models.Index(fields=['user', 'created_at'], name='api_key_au_user_id_a86a24_idx'),
        ),
        migrations.AddIndex(
            model_name='apikeyaudit',
            index=models.Index(fields=['api_key', 'created_at'], name='api_key_au_api_key_18ce73_idx'),
        ),
        migrations.AddIndex(
            model_name='apikeyaudit',
            index=models.Index(fields=['action', 'created_at'], name='api_key_au_action_f7b3e2_idx'),
        ),
        migrations.AddIndex(
            model_name='apikeyaudit',
            index=models.Index(fields=['ip_address', 'created_at'], name='api_key_au_ip_addr_8a4c5d_idx'),
        ),
        migrations.AddIndex(
            model_name='apikeyaudit',
            index=models.Index(fields=['success', 'created_at'], name='api_key_au_success_b2e7f1_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='apikey',
            unique_together={('user', 'name')},
        ),
    ]