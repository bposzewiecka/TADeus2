# Generated by Django 2.0.3 on 2021-04-24 18:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tadeus', '0004_auto_20210424_1544'),
    ]

    operations = [
        migrations.RenameField(
            model_name='track',
            old_name='hic_display_options',
            new_name='hic_display',
        ),
    ]
