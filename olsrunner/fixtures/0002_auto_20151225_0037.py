# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-25 05:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olsrunner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='PlayerID',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='player',
            name='username',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
