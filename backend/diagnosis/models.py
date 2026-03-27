from django.db import models
from django.contrib.auth.models import User

class Diagnosis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    image = models.ImageField(upload_to='uploads/')
    
    prediction = models.CharField(max_length=100)
    confidence = models.FloatField()
    risk_level = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.prediction} ({self.confidence}%)"
