from django.contrib import admin

from .models import ScanResult


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "uploaded_by", "prediction", "confidence", "risk_level", "created_at")
    list_filter = ("prediction", "risk_level", "scan_type", "created_at")
    search_fields = ("patient__username", "patient__patient_id", "patient__first_name", "patient__last_name")
