# Generated by Django 5.1.2 on 2024-11-02 22:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("course", "0003_alter_course_description_alter_course_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Module",
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
                ("is_visible", models.BooleanField(default=True)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="modules",
                        to="course.course",
                    ),
                ),
            ],
        ),
    ]
