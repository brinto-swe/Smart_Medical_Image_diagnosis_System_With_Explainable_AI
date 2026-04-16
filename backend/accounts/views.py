from rest_framework.decorators import api_view, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password
from .models import User
from diagnosis.permissions import IsAdmin



@api_view(['POST'])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if user:
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "role": user.role,
            "username": user.username
        })

    return Response({"error": "Invalid credentials"}, status=400)


# ✅ Create Doctor
@api_view(['POST'])
@permission_classes([IsAdmin])
def create_doctor(request):
    try:
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "username & password required"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        doctor = User.objects.create(
            username=username,
            password=make_password(password),
            role="doctor"
        )

        return Response({
            "message": "Doctor created successfully",
            "doctor_id": doctor.id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAdmin])
def get_doctors(request):
    doctors = User.objects.filter(role="doctor")

    data = [
        {
            "id": d.id,
            "username": d.username
        }
        for d in doctors
    ]

    return Response(data)

@api_view(['DELETE'])
@permission_classes([IsAdmin])
def delete_doctor(request, doctor_id):
    try:
        doctor = User.objects.get(id=doctor_id, role="doctor")
        doctor.delete()
        return Response({"message": "Doctor deleted"})
    except User.DoesNotExist:
        return Response({"error": "Doctor not found"}, status=404)
    

@api_view(['PUT'])
@permission_classes([IsAdmin])
def update_doctor(request, doctor_id):
    try:
        doctor = User.objects.get(id=doctor_id, role="doctor")

        doctor.username = request.data.get("username", doctor.username)

        if request.data.get("password"):
            doctor.password = make_password(request.data.get("password"))

        doctor.save()

        return Response({"message": "Doctor updated"})

    except User.DoesNotExist:
        return Response({"error": "Doctor not found"}, status=404)
