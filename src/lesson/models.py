from django.db import models

from authentication.models import User
from module.models import Module

class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    topic = models.CharField(max_length=255)
    order = models.PositiveIntegerField()

    @classmethod
    def get_next_order(cls, module_id):
        last_order = cls.objects.filter(module_id=module_id).aggregate(models.Max('order'))['order__max']
        return (last_order or 0) + 1
    
    def __str__(self):
        return f"{self.name} (Order: {self.order})"


    def get_introduction(self):
        """Retrieve the introduction of the lesson."""
        if hasattr(self, "lesson_introduction"):
            return {
                "id": self.lesson_introduction.id,
                "description": self.lesson_introduction.description
            }
        return None

    
    def get_quizzes(self) -> list:
        """Retrieve all quizzes associated with this lesson."""
        if hasattr(self, "lesson_quiz"):
            return [
                {
                    "id": quiz.id,
                    "question": quiz.question,
                    "answers": [
                        {
                            "id": option.id,
                            "answer": option.answer,
                            "is_correct": option.is_correct
                        }
                        for option in quiz.options.all()
                    ],
                }
                for quiz in self.lesson_quiz.all()
            ]
        return []

    def get_assignment(self) -> dict:
        """Retrieve the assignment associated with this lesson dynamically."""
        if hasattr(self, "lesson_assignment"):
            return {
                "id": self.lesson_assignment.id,
                "instructions": self.lesson_assignment.instructions,
                # "started_count": self.assignment.started_count,
                # "completed_count": self.assignment.completed_count,
                # "average_score": self.assignment.average_score
            }
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "topic": self.topic,
            "order": self.order,
            "introduction": self.get_introduction(),
            "quiz": self.get_quizzes(),
            "assignment": self.get_assignment(),
        }
    

class StudentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    introduction_completed = models.BooleanField(default=False)
    quiz_score = models.FloatField(null=True, blank=True)
    assignment_score = models.FloatField(null=True, blank=True)
    lesson_completed = models.BooleanField(default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "student": self.user,
            "lesson": self.lesson,
            "introduction_completed": self.introduction_completed,
            "quiz_score": self.quiz_score,
            "assignment_score": self.assignment_score,
            "lesson_completed": self.lesson_completed

        }