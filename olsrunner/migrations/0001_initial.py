# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-30 02:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team1', models.IntegerField(default=0)),
                ('team2', models.IntegerField(default=0)),
                ('winner', models.IntegerField(default=0)),
                ('Number', models.IntegerField(default=0)),
                ('filename', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('SummonerNumber', models.IntegerField(default=0)),
                ('PlayerIGN', models.CharField(max_length=30)),
                ('PlayerName', models.CharField(max_length=50)),
                ('IsCaptain', models.BooleanField(default=False)),
                ('username', models.CharField(blank=True, max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Stats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('PlayerID', models.IntegerField(default=0)),
                ('Kills', models.IntegerField(blank=True, default=0)),
                ('Deaths', models.IntegerField(blank=True, default=0)),
                ('Assists', models.IntegerField(blank=True, default=0)),
                ('GoldTotal', models.IntegerField(blank=True, default=0)),
                ('GamesPlayed', models.IntegerField(blank=True, default=0)),
                ('LargestCrit', models.IntegerField(blank=True, default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teamID', models.IntegerField(default=0)),
                ('teamName', models.CharField(max_length=100)),
                ('Captain', models.CharField(max_length=20)),
                ('Player1', models.CharField(max_length=20)),
                ('Player2', models.CharField(max_length=20)),
                ('Player3', models.CharField(max_length=20)),
                ('Player4', models.CharField(max_length=20)),
                ('CaptainID', models.IntegerField(default=0)),
                ('Player1ID', models.IntegerField(default=0)),
                ('Player2ID', models.IntegerField(default=0)),
                ('Player3ID', models.IntegerField(default=0)),
                ('Player4ID', models.IntegerField(default=0)),
            ],
        ),
    ]
