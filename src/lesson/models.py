from django.db import models

from module.models import Module

class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField()

    @classmethod
    def get_next_order(cls, module_id):
        last_order = cls.objects.filter(module_id=module_id).aggregate(models.Max('order'))['order__max']
        return (last_order or 0) + 1
    
    def __str__(self):
        return f"{self.name} (Order: {self.order})"
    
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
        }