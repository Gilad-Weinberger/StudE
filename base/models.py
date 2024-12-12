from django.db import models
from users.models import User

class Class(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} ({self.user})"

class Assignment(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'), 
        ('done', 'Done'),
        ('submitted', 'Submitted'),
        ('not_submitted', 'Not Submitted')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=200, choices=STATUS_CHOICES, default='not_started', null=True, blank=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        due_date_str = self.due_date.strftime('%d/%m/%Y %H:%M') if self.due_date else 'No due date'
        class_name = self.class_obj if self.class_obj else 'No class'
        return f"{self.name} | {class_name} | {due_date_str}"
    
class Exam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name} | {self.class_obj} | {self.date.strftime('%d/%m/%Y')}"

