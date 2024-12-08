from django.contrib import admin

from .models import StudentProgress

# Register your models here.

class StidentProgressAdmin(admin.ModelAdmin):
    model: StudentProgress
    fields: {"id"}

admin.site.register(StudentProgress)