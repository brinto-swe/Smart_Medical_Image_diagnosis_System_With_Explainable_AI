from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP
from .serializers import (
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    SignupSerializer,
    UserProfileSerializer,
)
from .utils import ensure_group_identifiers, generate_identifier, set_user_group
from diagnosis.permissions import IsAdminUserGroup


User = get_user_model()


def users_in_group(group_name):
    ensure_group_identifiers(group_name)
    return User.objects.filter(groups__name=group_name).order_by("id")


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(pk=response.data["id"])
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserProfileSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"error": "User account is disabled."}, status=status.HTTP_403_FORBIDDEN)

        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserProfileSerializer(user, context={"request": request}).data,
                "role": user.role,
                "dashboard": user.dashboard,
            }
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"message": "Logged out successfully."})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.must_change_password = False
        request.user.save(update_fields=["password", "must_change_password"])
        Token.objects.filter(user=request.user).delete()
        return Response({"message": "Password changed successfully. Please login again."})


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            api_path = reverse("password-reset-confirm")
            reset_url = getattr(settings, "FRONTEND_PASSWORD_RESET_URL", "")
            if reset_url:
                link = f"{reset_url}?uid={uid}&token={token}"
            else:
                link = request.build_absolute_uri(api_path)
                link = f"{link}?uid={uid}&token={token}"

            send_mail(
                "Reset your MediCare password",
                f"Use this link to reset your password: {link}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        return Response({"message": "If the email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data["token"]
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        Token.objects.filter(user=user).delete()
        return Response({"message": "Password reset successfully."})


class DoctorListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUserGroup]

    def get_queryset(self):
        return users_in_group(DOCTOR_GROUP)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminUserCreateSerializer
        return UserProfileSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["group_name"] = DOCTOR_GROUP
        return context


class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminUserUpdateSerializer
    permission_classes = [IsAdminUserGroup]

    def get_queryset(self):
        return users_in_group(DOCTOR_GROUP)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        return Response(UserProfileSerializer(user, context={"request": request}).data)

    def perform_update(self, serializer):
        user = serializer.save()
        if not user.groups.filter(name=DOCTOR_GROUP).exists():
            set_user_group(user, DOCTOR_GROUP)


class PatientListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUserGroup]

    def get_queryset(self):
        queryset = users_in_group(PATIENT_GROUP)
        query = self.request.query_params.get("q")
        if query:
            queryset = queryset.filter(
                models.Q(patient_id__icontains=query)
                | models.Q(first_name__icontains=query)
                | models.Q(last_name__icontains=query)
                | models.Q(email__icontains=query)
                | models.Q(phone_number__icontains=query)
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminUserCreateSerializer
        return UserProfileSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["group_name"] = PATIENT_GROUP
        return context


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminUserUpdateSerializer
    permission_classes = [IsAdminUserGroup]

    def get_queryset(self):
        return users_in_group(PATIENT_GROUP)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        return Response(UserProfileSerializer(user, context={"request": request}).data)

    def perform_update(self, serializer):
        user = serializer.save()
        if not user.groups.filter(name=PATIENT_GROUP).exists():
            set_user_group(user, PATIENT_GROUP)


class RoleChangeView(APIView):
    permission_classes = [IsAdminUserGroup]

    def post(self, request, user_id):
        role = request.data.get("role")
        role_map = {
            "admin": ADMIN_GROUP,
            "doctor": DOCTOR_GROUP,
            "patient": PATIENT_GROUP,
            ADMIN_GROUP: ADMIN_GROUP,
            DOCTOR_GROUP: DOCTOR_GROUP,
            PATIENT_GROUP: PATIENT_GROUP,
        }
        group_name = role_map.get(role)
        if not group_name:
            return Response({"error": "role must be admin, doctor, or patient."}, status=400)
        user = get_object_or_404(User, pk=user_id)
        update_fields = []
        if group_name == DOCTOR_GROUP and not user.doctor_id:
            user.doctor_id = generate_identifier("D", "doctor_id")
            update_fields.append("doctor_id")
        if group_name == PATIENT_GROUP and not user.patient_id:
            user.patient_id = generate_identifier("P", "patient_id")
            update_fields.append("patient_id")
        if update_fields:
            user.save(update_fields=update_fields)
        set_user_group(user, group_name)
        return Response(UserProfileSerializer(user, context={"request": request}).data)
