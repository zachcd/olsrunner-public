# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-06 21:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olsrunner', '0006_team_league'),
    ]

    operations = [
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('L0game1', models.IntegerField(default=0)),
                ('L0game2', models.IntegerField(default=0)),
                ('L0game3', models.IntegerField(default=0)),
                ('L1game1', models.IntegerField(default=0)),
                ('L1game2', models.IntegerField(default=0)),
                ('L1game3', models.IntegerField(default=0)),
                ('L2game1', models.IntegerField(default=0)),
                ('L2game2', models.IntegerField(default=0)),
                ('L2game3', models.IntegerField(default=0)),
                ('L3game1', models.IntegerField(default=0)),
                ('L3game2', models.IntegerField(default=0)),
                ('L3game3', models.IntegerField(default=0)),
            ],
        ),
    ]
