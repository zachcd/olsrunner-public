# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-05 01:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('olsrunner', '0003_auto_20160102_2038'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stats',
            old_name='MinutesPlayed',
            new_name='SecondsPlayed',
        ),
    ]
