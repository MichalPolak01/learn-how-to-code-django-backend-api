from django.contrib import admin

from .models import Course, Rating

class CourseAdmin(admin.ModelAdmin):
    model = Course
    list_display = ("id", "name", "author", "last_updated", "is_public")


admin.site.register(Course, CourseAdmin)