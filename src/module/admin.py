from django.contrib import admin

from .models import Module

class ModuleAdmin(admin.ModelAdmin):
    model = Module
    list_display = ("id", "name", "course")


admin.site.register(Module, ModuleAdmin)