from django.db import models
from lesson.models import Lesson
from authentication.models import User

class LessonIntroduction(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='lesson_introduction')
    description = models.TextField()
    
    
class LessonQuiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='lesson_quiz')
    question = models.TextField()

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
        }


class QuizOption(models.Model):
    question = models.ForeignKey(LessonQuiz, on_delete=models.CASCADE, related_name='options')
    answer = models.TextField()
    is_correct = models.BooleanField()

    def to_dict(self):
        return {
            "id": self.id,
            "answer": self.option,
            "is_correct": self.is_correct,
        }


class LessonAssignment(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='lesson_assignment')
    instructions = models.TextField()
    started_count = models.IntegerField(default=0)
    completed_count = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "instructions": self.instructions,
            "started_count": self.started_count,
            "completed_count": self.completed_count,
            "average_score": self.average_score,
        }


class UsserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    description_completed = models.BooleanField(default=False)
    quiz_score = models.FloatField(null=True, blank=True)
    assignment_completed = models.BooleanField(default=False)
    assignment_score = models.FloatField(null=True, blank=True)