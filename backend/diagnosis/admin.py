from django.contrib import admin

from .models import DoctorAssignment, MedicalReport, ScanResult


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "uploaded_by", "prediction", "confidence", "risk_level", "created_at")
    list_filter = ("prediction", "risk_level", "scan_type", "created_at")
    search_fields = ("patient__username", "patient__patient_id", "patient__first_name", "patient__last_name")


@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ("id", "scan", "patient", "doctor", "generated_at")
    search_fields = ("patient__username", "patient__patient_id", "patient__first_name", "patient__last_name")


@admin.register(DoctorAssignment)
class DoctorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "scheduled_at", "assigned_by")
    list_filter = ("scheduled_at", "doctor")
    search_fields = (
        "patient__username",
        "patient__patient_id",
        "patient__first_name",
        "patient__last_name",
        "doctor__username",
        "doctor__doctor_id",
        "doctor__first_name",
        "doctor__last_name",
    )
