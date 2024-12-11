from django.db import models
from users.models import User

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    time = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.time.strftime('%d/%m/%Y %H:%M')}"
    
class Task(models.Model):
    OBJECT_CHOICES = [
        ("class", "Class"),
        ("assignment", "Assignment"),
        ("exam", "Exam"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    object = models.CharField(max_length=255, choices=OBJECT_CHOICES, null=True, blank=True)
    properties = models.JSONField(default=dict, null=True, blank=True)
    start_date = models.DateField(auto_now_add=True)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.object} - {self.start_date}"
