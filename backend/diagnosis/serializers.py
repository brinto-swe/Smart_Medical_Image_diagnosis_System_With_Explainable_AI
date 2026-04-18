from rest_framework import serializers

from .models import ScanResult


class ScanResultSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_id = serializers.CharField(source="patient.patient_id", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    original_image_url = serializers.SerializerMethodField()
    heatmap_image_url = serializers.SerializerMethodField()

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
