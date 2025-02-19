# Generated by Django 5.1.2 on 2024-11-25 22:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lesson", "0001_initial"),
        ("lesson_content", "0004_alter_lessonassigment_lesson"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="LessonQuiz",
            new_name="LessonQuestion",
        ),
        migrations.RenameField(
            model_name="quizoption",
            old_name="quiz",
            new_name="question",
        ),
        migrations.CreateModel(
            name="LessonIntroduction",
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
                ("introduction", models.TextField()),
                (
                    "lesson",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lesson_introduction",
                        to="lesson.lesson",
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="LessonDescription",
        ),
    ]
