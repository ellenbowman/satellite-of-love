# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('satellite', '0021_auto_20150609_1638'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticker',
            name='coverage_type',
            field=models.IntegerField(default=0, choices=[(1, b'10% Promise'), (2, b'5 and 3'), (3, b'Earnings Preview'), (4, b'Earnings Review'), (5, b'Risk Rating')]),
            preserve_default=True,
        ),
    ]
