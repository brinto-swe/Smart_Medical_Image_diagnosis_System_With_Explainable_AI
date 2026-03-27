from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import os

from .models import Diagnosis
from .serializers import DiagnosisSerializer

from ai_models.chest_xray.inference import predict_image

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_view(request):
    if 'image' not in request.FILES:
        return Response({'error': 'No image uploaded'}, status=400)

    image = request.FILES['image']

    # Save temporarily
    upload_path = os.path.join(settings.MEDIA_ROOT, image.name)
    with open(upload_path, 'wb+') as destination:
        for chunk in image.chunks():
            destination.write(chunk)

    # Run inference
    result = predict_image(upload_path)

    # Save to database
    diagnosis = Diagnosis.objects.create(
        user=request.user,
        image=image,
        prediction=result['prediction'],
        confidence=result['confidence'],
        risk_level=result['risk_level']
    )

    serializer = DiagnosisSerializer(diagnosis)

    return Response(serializer.data)
