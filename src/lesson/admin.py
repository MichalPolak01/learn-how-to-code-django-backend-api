from django.contrib import admin

from .models import StudentProgress


class StidentProgressAdmin(admin.ModelAdmin):
    model: StudentProgress
    fields: {"id"}

admin.site.register(StudentProgress)