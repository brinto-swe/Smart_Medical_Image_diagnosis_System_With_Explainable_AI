from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from djoser import signals
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .email_utils import send_activation_email, send_password_reset_email
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        signals.user_registered.send(sender=self.__class__, user=user, request=request)
        send_activation_email(request, user)
        return Response(
            {
                "message": "Registration successful. Please check your email to activate your account.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = (request.data.get("username") or request.data.get("email") or "").strip()
        password = request.data.get("password")
        matched_user = User.objects.filter(email__iexact=identifier).first()
        login_username = matched_user.username if matched_user else identifier
        user = authenticate(request, username=login_username, password=password)
        if not user:
            inactive_user = matched_user or User.objects.filter(username=identifier).first()
            if inactive_user and not inactive_user.is_active and inactive_user.check_password(password):
                return Response(
                    {"error": "Please activate your account from the verification email before logging in."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response(
                {"error": "Please activate your account from the verification email before logging in."},
                status=status.HTTP_403_FORBIDDEN,
            )

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
            send_password_reset_email(request, user)
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


class ActivateAccountLinkView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, uid, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            if user.is_active or not default_token_generator.check_token(user, token):
                raise ValueError("invalid activation token")
            user.is_active = True
            user.save(update_fields=["is_active"])
            signals.user_activated.send(sender=self.__class__, user=user, request=request)
            message = (
                "<h2>Account activated successfully</h2>"
                "<p>Your patient account is now active. You can return to the MediCare desktop app and sign in.</p>"
            )
        except Exception:
            message = (
                "<h2>Activation link is invalid or already used</h2>"
                "<p>Please request a new activation email or contact support if the problem continues.</p>"
            )

        return HttpResponse(
            f"""
            <html>
              <head>
                <title>MediCare Activation</title>
                <style>
                  body {{
                    font-family: Arial, Helvetica, sans-serif;
                    background: #f6f8fb;
                    color: #1f2937;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                  }}
                  .card {{
                    background: white;
                    border: 1px solid #e5eaf0;
                    border-radius: 12px;
                    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
                    padding: 32px;
                    max-width: 520px;
                  }}
                  h2 {{
                    margin-top: 0;
                    color: #0f172a;
                  }}
                  p {{
                    color: #526175;
                    line-height: 1.6;
                  }}
                </style>
              </head>
              <body>
                <div class="card">{message}</div>
              </body>
            </html>
            """
        )


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
