from ai_models.chest_xray.inference import predict
import os
import cv2

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.conf import settings
from django.core.files.base import ContentFile

from .models import ScanResult, Patient
from .serializers import ScanResultSerializer, PatientSerializer
from .permissions import IsDoctor, IsAdmin


# ✅ Create Patient
@api_view(['POST'])
@permission_classes([IsDoctor])
def create_patient(request):
    serializer = PatientSerializer(data=request.data)
    if serializer.is_valid():
        patient = serializer.save()
        return Response({"message": "Patient created", "patient_id": patient.id})
    return Response(serializer.errors, status=400)


# ✅ Predict + Save Scan
@api_view(['POST'])
@permission_classes([IsDoctor])
def predict_view(request):
    try:
        image = request.FILES.get('image')
        patient_id = request.data.get('patient_id')

        if not image or not patient_id:
            return Response({"error": "image and patient_id required"}, status=400)

        patient = Patient.objects.get(id=patient_id)

        # save temp
        temp_path = os.path.join(settings.MEDIA_ROOT, image.name)
        with open(temp_path, 'wb+') as f:
            for chunk in image.chunks():
                f.write(chunk)

        # AI prediction
        result = predict(temp_path)

        # save heatmap
        heatmap_filename = f"heatmap_{image.name}"
        heatmap_path = os.path.join(settings.MEDIA_ROOT, heatmap_filename)
        cv2.imwrite(heatmap_path, result["heatmap"])

        with open(heatmap_path, "rb") as f:
            scan = ScanResult.objects.create(
                patient=patient,
                uploaded_by=request.user,
                original_image=image,
                heatmap_image=ContentFile(f.read(), name=heatmap_filename),
                prediction=result["prediction"],
                confidence=result["confidence"],
                risk_level=result["risk_level"],
                explanation={
                    "note": "Grad-CAM visualization generated",
                    "model": "MSA-HCNN"
                }
            )

        serializer = ScanResultSerializer(scan)
        return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ✅ Get All Scans
@api_view(['GET'])
def all_scans(request):
    scans = ScanResult.objects.all().order_by('-created_at')
    serializer = ScanResultSerializer(scans, many=True)
    return Response(serializer.data)


# ✅ Recent Scans (Dashboard)
@api_view(['GET'])
def recent_scans(request):
    scans = ScanResult.objects.all().order_by('-created_at')[:5]
    serializer = ScanResultSerializer(scans, many=True)
    return Response(serializer.data)


# ✅ Patient History
@api_view(['GET'])
def patient_history(request, patient_id):
    scans = ScanResult.objects.filter(patient_id=patient_id).order_by('-created_at')
    serializer = ScanResultSerializer(scans, many=True)
    return Response(serializer.data)


# ✅ Search Patient
@api_view(['GET'])
def search_patient(request):
    query = request.GET.get('q', '')
    patients = Patient.objects.filter(name__icontains=query)
    serializer = PatientSerializer(patients, many=True)
    return Response(serializer.data)


# ✅ Report (Admin Only)
@api_view(['GET'])
@permission_classes([IsAdmin])
def generate_report(request, scan_id):
    scan = ScanResult.objects.get(id=scan_id)

    report = {
        "patient_id": scan.patient.id,
        "prediction": scan.prediction,
        "confidence": scan.confidence,
        "risk_level": scan.risk_level,
        "date": scan.created_at,
        "summary": f"{scan.prediction} detected with {scan.confidence*100:.1f}% confidence.",
        "recommendation": "Consult a specialist."
    }

    return Response(report)


# ✅ Scan Detail
@api_view(['GET'])
def scan_detail(request, scan_id):
    scan = ScanResult.objects.get(id=scan_id)

    serializer = ScanResultSerializer(scan)
    return Response(serializer.data)

