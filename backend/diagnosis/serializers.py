from rest_framework import serializers

from .models import MedicalReport, ScanResult


class ScanResultSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_id = serializers.CharField(source="patient.patient_id", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    original_image_url = serializers.SerializerMethodField()
    heatmap_image_url = serializers.SerializerMethodField()
    report_id = serializers.SerializerMethodField()
    report_pdf_url = serializers.SerializerMethodField()
    has_report = serializers.SerializerMethodField()

    class Meta:
        model = ScanResult
        fields = [
            "id",
            "patient",
            "patient_id",
            "patient_name",
            "uploaded_by",
            "uploaded_by_name",
            "original_image",
            "original_image_url",
            "heatmap_image",
            "heatmap_image_url",
            "has_report",
            "report_id",
            "report_pdf_url",
            "prediction",
            "confidence",
            "risk_level",
            "scan_type",
            "result_json",
            "explanation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_patient_name(self, obj):
        return obj.patient.get_full_name() or obj.patient.username

    def get_uploaded_by_name(self, obj):
        if not obj.uploaded_by:
            return None
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

    def build_file_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get("request")
        url = file_field.url
        return request.build_absolute_uri(url) if request else url

    def get_original_image_url(self, obj):
        return self.build_file_url(obj.original_image)

    def get_heatmap_image_url(self, obj):
        return self.build_file_url(obj.heatmap_image)

    def get_has_report(self, obj):
        return hasattr(obj, "medical_report") and bool(obj.medical_report.report_pdf)

    def get_report_id(self, obj):
        return obj.medical_report.id if hasattr(obj, "medical_report") else None

    def get_report_pdf_url(self, obj):
        if not hasattr(obj, "medical_report") or not obj.medical_report.report_pdf:
            return None
        return self.build_file_url(obj.medical_report.report_pdf)


class MedicalReportSerializer(serializers.ModelSerializer):
    patient_id = serializers.CharField(source="patient.patient_id", read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    scan = ScanResultSerializer(read_only=True)

    class Meta:
        model = MedicalReport
        fields = [
            "id",
            "scan",
            "patient_id",
            "patient_name",
            "doctor_name",
            "pdf_url",
            "generated_at",
        ]

    def get_patient_name(self, obj):
        return obj.patient.get_full_name() or obj.patient.username

    def get_doctor_name(self, obj):
        if not obj.doctor:
            return ""
        return obj.doctor.get_full_name() or obj.doctor.username

    def get_pdf_url(self, obj):
        if not obj.report_pdf:
            return None
        request = self.context.get("request")
        url = obj.report_pdf.url
        return request.build_absolute_uri(url) if request else url
