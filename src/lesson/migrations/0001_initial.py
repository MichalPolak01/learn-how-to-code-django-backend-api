# Generated by Django 5.1.2 on 2024-11-03 16:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("module", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Lesson",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("order", models.PositiveIntegerField()),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lessons",
                        to="module.module",
                    ),
                ),
            ],
        ),
    ]
