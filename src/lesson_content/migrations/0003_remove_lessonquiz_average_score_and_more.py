# Generated by Django 5.1.1 on 2024-11-21 17:55

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("lesson_content", "0002_alter_lessonassigment_lesson_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lessonquiz",
            name="average_score",
        ),
        migrations.RemoveField(
            model_name="lessonquiz",
            name="completed_count",
        ),
        migrations.RemoveField(
            model_name="lessonquiz",
            name="started_count",
        ),
    ]
