from django.db import models

from course.models import Course

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    is_visible = models.BooleanField(default=True)

    @classmethod
    def get_next_order(cls, course_id):
        last_order = cls.objects.filter(course_id=course_id).aggregate(models.Max('order'))['order__max']
        return (last_order or 0) + 1
    
    def __str__(self):
        return f"{self.name} (Order: {self.order})"
    
    def get_lesson_count(self):
        try:
            return self.lessons.count()
        except:
            return 0
        
    # def get_lessons(self):
    #     return [
    #         {
    #             "id": lesson.id,
    #             "name": lesson.name,
    #             "order": lesson.order,
    #             # "description": lesson.get_description(),
    #             # "quiz": lesson.quiz,
    #             # "assignment": lesson.assignment,
    #         }
    #         for lesson in self.lessons.all().order_by("order")
    #     ]

    # def get_lessons(self):
    #     return [lesson.to_dict() for lesson in self.lessons.all().order_by("order")]

    # def get_lessons(self):
    #     return [lesson.to_dict() for lesson in self.lessons.all().order_by("order")]

    def get_lessons(self):
        """Retrieve all lessons with their details."""
        return [lesson.to_dict() for lesson in self.lessons.all().order_by("order")]

        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "is_visible": self.is_visible,
            "lesson_count": self.get_lesson_count(),
            "lessons": self.get_lessons()
        }