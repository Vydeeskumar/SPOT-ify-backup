# Generated by Django 5.2.3 on 2025-07-04 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0009_dailysong"),
    ]

    operations = [
        migrations.AddField(
            model_name="song",
            name="spotify_duplicates",
            field=models.TextField(blank=True, default=""),
        ),
    ]
