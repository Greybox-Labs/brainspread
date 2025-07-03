# Generated manually to drop unused WebSearchConfig table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_chat', '0007_rename_default_to_preferred_model'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS ai_chat_web_search_config CASCADE;",
            reverse_sql="-- Cannot reverse this migration",
        ),
    ]