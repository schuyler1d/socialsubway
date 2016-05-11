# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-04 23:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mosaicrenderer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TweeterBlocklist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='TweetMosaicSource',
            fields=[
                ('mosaicsourceimage_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mosaicrenderer.MosaicSourceImage')),
                ('message', models.TextField(default='', help_text='maybe not always the full message/post')),
                ('useralias', models.CharField(help_text='aka username of service', max_length=128)),
                ('link', models.URLField(blank=True)),
                ('geo', models.CharField(max_length=128)),
            ],
            bases=('mosaicrenderer.mosaicsourceimage',),
        ),
        migrations.CreateModel(
            name='TwitterCollector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('access_token_secret', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TwitterMosaic',
            fields=[
                ('mosaic_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mosaicrenderer.Mosaic')),
                ('twitter_search', models.TextField(blank=True)),
                ('collector', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='twittercollector.TwitterCollector')),
            ],
            bases=('mosaicrenderer.mosaic',),
        ),
    ]