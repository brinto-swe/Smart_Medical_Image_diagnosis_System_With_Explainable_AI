from ai_models.chest_xray.inference import predict
import os
import sys
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from .models import ScanResult, Patient
from .serializers import ScanResultSerializer

# 🔥 AI import fix
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)


@api_view(['POST'])
def create_patient(request):
    try:
        name = request.data.get("name")
        age = request.data.get("age")
        gender = request.data.get("gender")

        if not name or not age or not gender:
            return Response({"error": "name, age, gender required"}, status=400)

        patient = Patient.objects.create(
            name=name,
            age=age,
            gender=gender
        )

        return Response({
            "message": "Patient created",
            "patient_id": patient.id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def predict_view(request):
    try:
        image = request.FILES.get('image')
        patient_id = request.data.get('patient_id')

        if not image or not patient_id:
            return Response({"error": "image and patient_id required"}, status=400)

        # 🔥 get or create patient
        patient = Patient.objects.get(id=patient_id)

        # 🔥 save original image temporarily
        temp_path = os.path.join(settings.MEDIA_ROOT, image.name)

        with open(temp_path, 'wb+') as f:
            for chunk in image.chunks():
                f.write(chunk)

        # 🔥 AI prediction
        result = predict(temp_path)

        # 🔥 save heatmap
        heatmap_filename = f"heatmap_{image.name}"
        heatmap_path = os.path.join(settings.MEDIA_ROOT, heatmap_filename)

        import cv2
        cv2.imwrite(heatmap_path, result["heatmap"])

        # 🔥 save to DB
        scan = ScanResult.objects.create(
            patient=patient,
            uploaded_by=request.user if request.user.is_authenticated else None,
            original_image=image,
            heatmap_image=heatmap_filename,
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


@api_view(['GET'])
def patient_history(request, patient_id):
    try:
        scans = ScanResult.objects.filter(
            patient_id=patient_id).order_by('-created_at')
        serializer = ScanResultSerializer(scans, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def search_patient(request):
    query = request.GET.get('q', '')

    patients = Patient.objects.filter(name__icontains=query)

    data = []
    for p in patients:
        data.append({
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "gender": p.gender
        })

    return Response(data)

@api_view(['GET'])
def generate_report(request, scan_id):
    try:
        scan = ScanResult.objects.get(id=scan_id)

        report = {
            "patient_id": scan.patient.id,
            "prediction": scan.prediction,
            "confidence": scan.confidence,
            "risk_level": scan.risk_level,
            "date": scan.created_at,
            "summary": f"{scan.prediction} detected with {scan.confidence*100:.1f}% confidence.",
            "recommendation": "Consult a specialist for further diagnosis."
        }

        return Response(report)

    except Exception as e:
        return Response({"error": str(e)}, status=500)