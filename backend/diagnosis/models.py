from django.db import models
from django.conf import settings


class Patient(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ScanResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    original_image = models.ImageField(upload_to="original/")
    heatmap_image = models.ImageField(upload_to="heatmaps/")

    prediction = models.CharField(max_length=50)
    confidence = models.FloatField()
    risk_level = models.CharField(max_length=20)

    explanation = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.prediction}"

