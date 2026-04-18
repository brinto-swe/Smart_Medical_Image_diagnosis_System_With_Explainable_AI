import os
import tempfile

import cv2
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP
from accounts.serializers import UserProfileSerializer
from accounts.utils import user_has_group
from ai_models.chest_xray.inference import predict

from .models import ScanResult
from .permissions import IsAdminDoctorOrPatient, IsAdminOrDoctor, IsAdminUserGroup, IsDoctorUserGroup
from .serializers import ScanResultSerializer


User = get_user_model()


def patient_queryset():
    return User.objects.filter(groups__name=PATIENT_GROUP).order_by("patient_id", "id")


def scan_queryset_for_user(user):
    queryset = ScanResult.objects.select_related("patient", "uploaded_by").order_by("-created_at")
    if user_has_group(user, ADMIN_GROUP) or user_has_group(user, DOCTOR_GROUP):
        return queryset
    return queryset.filter(patient=user)


class DoctorPatientSearchView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsDoctorUserGroup]

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        queryset = patient_queryset()
        if query:
            queryset = queryset.filter(
                Q(patient_id__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(phone_number__icontains=query)
            )
        return queryset


class PredictXrayView(APIView):
    permission_classes = [IsDoctorUserGroup]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        image = request.FILES.get("image")
        patient_identifier = request.data.get("patient_id")

        if not image or not patient_identifier:
            return Response({"error": "image and patient_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        patient = get_object_or_404(User, patient_id=patient_identifier, groups__name=PATIENT_GROUP)

        suffix = os.path.splitext(image.name)[1] or ".jpg"
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_path = temp_file.name
                for chunk in image.chunks():
                    temp_file.write(chunk)

            result = predict(temp_path)
            heatmap_success, heatmap_buffer = cv2.imencode(".jpg", result["heatmap"])
            if not heatmap_success:
                return Response({"error": "Could not generate heatmap image."}, status=500)

            image.seek(0)
            scan = ScanResult.objects.create(
                patient=patient,
                uploaded_by=request.user,
                original_image=image,
                prediction=result["prediction"],
                confidence=result["confidence"],
                risk_level=result["risk_level"],
                result_json={
                    "prediction": result["prediction"],
                    "confidence": result["confidence"],
                    "risk_level": result["risk_level"],
                },
                explanation={
                    "note": "Grad-CAM visualization generated",
                    "model": "MSA-HCNN",
                },
            )
            scan.heatmap_image.save(
                f"heatmap_scan_{scan.pk}.jpg",
                ContentFile(heatmap_buffer.tobytes()),
                save=True,
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

        serializer = ScanResultSerializer(scan, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ScanListView(generics.ListAPIView):
    serializer_class = ScanResultSerializer
    permission_classes = [IsAdminDoctorOrPatient]

    def get_queryset(self):
        return scan_queryset_for_user(self.request.user)


class RecentScanListView(generics.ListAPIView):
    serializer_class = ScanResultSerializer
    permission_classes = [IsAdminOrDoctor]

    def get_queryset(self):
        return scan_queryset_for_user(self.request.user)[:5]


class PatientHistoryView(generics.ListAPIView):
    serializer_class = ScanResultSerializer
    permission_classes = [IsAdminDoctorOrPatient]

    def get_queryset(self):
        patient_identifier = self.kwargs["patient_id"]
        if user_has_group(self.request.user, PATIENT_GROUP):
            return ScanResult.objects.filter(patient=self.request.user).order_by("-created_at")
        patient = get_object_or_404(User, patient_id=patient_identifier, groups__name=PATIENT_GROUP)
        return ScanResult.objects.filter(patient=patient).select_related("patient", "uploaded_by").order_by("-created_at")


class ScanDetailView(generics.RetrieveAPIView):
    serializer_class = ScanResultSerializer
    permission_classes = [IsAdminDoctorOrPatient]

    def get_queryset(self):
        return scan_queryset_for_user(self.request.user)


class ReportView(APIView):
    permission_classes = [IsAdminDoctorOrPatient]

    def get(self, request, scan_id):
        scan = get_object_or_404(scan_queryset_for_user(request.user), pk=scan_id)
        serializer = ScanResultSerializer(scan, context={"request": request})
        return Response(
            {
                "report_id": f"R{scan.id:03d}",
                "scan": serializer.data,
                "summary": f"{scan.prediction} detected with {scan.confidence * 100:.1f}% confidence.",
                "recommendation": "Consult a specialist for clinical interpretation.",
            }
        )


class AdminReportSummaryView(APIView):
    permission_classes = [IsAdminUserGroup]

    def get(self, request):
        scans = ScanResult.objects.all()
        total_patients = User.objects.filter(groups__name=PATIENT_GROUP).count()
        total_doctors = User.objects.filter(groups__name=DOCTOR_GROUP).count()
        return Response(
            {
                "total_patients": total_patients,
                "active_doctors": total_doctors,
                "xray_scans": scans.count(),
                "normal_results": scans.filter(prediction__iexact="NORMAL").count(),
                "needs_attention": scans.exclude(prediction__iexact="NORMAL").count(),
                "by_prediction": list(scans.values("prediction").annotate(total=Count("id")).order_by("prediction")),
            }
        )
