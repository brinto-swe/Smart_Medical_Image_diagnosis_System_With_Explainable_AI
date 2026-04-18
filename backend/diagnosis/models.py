from django.conf import settings
from django.db import models


class ScanResult(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_scans",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_scans",
    )

    original_image = models.ImageField(upload_to="original/")
    heatmap_image = models.ImageField(upload_to="heatmaps/", blank=True, null=True)

    prediction = models.CharField(max_length=50)
    confidence = models.FloatField()
    risk_level = models.CharField(max_length=20)
    scan_type = models.CharField(max_length=50, default="Chest X-Ray")

    result_json = models.JSONField(default=dict, blank=True)
    explanation = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        patient_name = self.patient.get_full_name() or self.patient.username
        return f"{patient_name} - {self.prediction}"
