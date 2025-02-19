from django.db import models

from authentication.models import User


class Course(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    author = models.ForeignKey(User, default=1, on_delete=models.SET_DEFAULT, related_name='courses')
    last_updated = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)
    creator_state = models.CharField(max_length=60, default='update')
    image = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.name
    
    def get_student_count(self):
        return self.students.count()
    
    @staticmethod
    def update_course_rating(course_id):
        """Update course statistics."""

        course = Course.objects.get(id=course_id)
        ratings = Rating.objects.filter(course=course)
        
        course.rating = sum(rating.score for rating in ratings) / ratings.count()
        
        course.save()

    def get_lesson_count(self):
        try:
            return sum(module.lessons.count() for module in self.modules.all())
        except:
            return 0
        
    def get_modules(self):
        """Retrieve all lessons with their details."""
        return [module.to_dict() for module in self.modules.all().order_by("order")]
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "last_updated": self.last_updated.isoformat(),
            "is_public": self.is_public,
            "rating": self.rating,
            "student_count": self.get_student_count(),
            "lesson_count": self.get_lesson_count(),
            "modules": self.get_modules(),
            "creator_state": self.creator_state,
            "image": self.image
        }


class Rating(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()

    class Meta:
        unique_together = ('course', 'user')

    def __str__(self):
        return f'{self.user} rated {self.course.name}: {self.score}'