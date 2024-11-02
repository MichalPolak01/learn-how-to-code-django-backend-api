from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='courses')
    last_updated = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)

    def __str__(self):
        return self.name
    
    def get_student_count(self):
        return self.students.count()
    
    def get_average_score(self):
        ratings = self.ratings.all()

        if ratings.exists():
            return sum(rating.score for rating in ratings) / ratings.count()
        return 0.0

        # TODO Modules and lesson stats
    # def get_module_count(self):
    #     return self.module.count()
    
    # def get_lesson_count(self):
    #     return self.lesson.count()


class Rating(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()

    class Meta:
        unique_together = ('course', 'user')

    def __str__(self):
        return f'{self.user} rated {self.course.name}: {self.score}'