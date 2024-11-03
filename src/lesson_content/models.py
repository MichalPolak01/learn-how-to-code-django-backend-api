from django.db import models
from lesson.models import Lesson
from authentication.models import User

class LessonDescription(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    description = models.TextField()
    
class LessonQuiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    question = models.TextField()
    started_count = models.IntegerField(default=0)
    completed_count = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)


class QuizOption(models.Model):
    quiz = models.ForeignKey(LessonQuiz, on_delete=models.CASCADE, related_name='options')
    option = models.TextField()
    is_correct = models.BooleanField()


class LessonAssigment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    instructions = models.TextField()
    started_count = models.IntegerField(default=0)
    completed_count = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)


class UsserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    description_completed = models.BooleanField(default=False)
    quiz_score = models.FloatField(null=True, blank=True)
    assignment_completed = models.BooleanField(default=False)
    assignment_score = models.FloatField(null=True, blank=True)