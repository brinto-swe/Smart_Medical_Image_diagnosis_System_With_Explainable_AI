from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP, User
from .utils import generate_identifier, set_user_group


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    dashboard = serializers.CharField(read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    electronic_signature_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "dashboard",
            "is_online",
            "profile_picture",
            "profile_picture_url",
            "electronic_signature",
            "electronic_signature_url",
            "phone_number",
            "patient_id",
            "doctor_id",
            "specialization",
            "age",
            "gender",
            "blood_type",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "primary_condition",
            "allergies",
            "must_change_password",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "role",
            "dashboard",
            "is_online",
            "patient_id",
            "doctor_id",
            "must_change_password",
            "date_joined",
        ]

    def get_profile_picture_url(self, obj):
        if not obj.profile_picture:
            return None
        request = self.context.get("request")
        url = obj.profile_picture.url
        return request.build_absolute_uri(url) if request else url

    def get_electronic_signature_url(self, obj):
        if not obj.electronic_signature:
            return None
        request = self.context.get("request")
        url = obj.electronic_signature.url
        return request.build_absolute_uri(url) if request else url

    def get_is_online(self, obj):
        return Token.objects.filter(user=obj).exists()


class SignupSerializer(DjoserUserCreateSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    age = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "age",
            "phone_number",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        email = (attrs.get("email") or "").strip()
        if not email:
            raise serializers.ValidationError({"email": "Email is required."})
        existing = User.objects.filter(email__iexact=email).first()
        if existing and existing.is_active:
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        if existing and not existing.groups.filter(name=PATIENT_GROUP).exists() and existing.groups.exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        if existing:
            self.existing_inactive_user = existing
            attrs["username"] = existing.username
        attrs["email"] = email
        if not (attrs.get("username") or "").strip():
            attrs["username"] = self._username_from_email(email)
        if existing:
            return attrs
        return super().validate(attrs)

    def _username_from_email(self, email):
        base = email.split("@", 1)[0].strip() or "patient"
        base = "".join(char for char in base if char.isalnum() or char in "._-") or "patient"
        username = base[:120]
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base[:110]}{suffix}"
        return username

    def perform_create(self, validated_data):
        existing = getattr(self, "existing_inactive_user", None)
        if existing:
            existing.email = validated_data.get("email", existing.email)
            existing.first_name = validated_data.get("first_name", existing.first_name)
            existing.last_name = validated_data.get("last_name", existing.last_name)
            existing.age = validated_data.get("age", existing.age)
            existing.phone_number = validated_data.get("phone_number", existing.phone_number)
            existing.is_active = False
            existing.set_password(validated_data["password"])
            if not existing.patient_id:
                existing.patient_id = generate_identifier("P", "patient_id")
            existing.save(
                update_fields=[
                    "email",
                    "first_name",
                    "last_name",
                    "age",
                    "phone_number",
                    "password",
                    "is_active",
                    "patient_id",
                ]
            )
            set_user_group(existing, PATIENT_GROUP)
            return existing

        user = super().perform_create(validated_data)
        user.patient_id = generate_identifier("P", "patient_id")
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.age = validated_data.get("age", user.age)
        user.phone_number = validated_data.get("phone_number", user.phone_number)
        user.save(
            update_fields=[
                "is_active",
                "patient_id",
                "first_name",
                "last_name",
                "age",
                "phone_number",
            ]
        )
        set_user_group(user, PATIENT_GROUP)
        return user


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "electronic_signature",
            "patient_id",
            "doctor_id",
            "specialization",
            "age",
            "gender",
            "blood_type",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "primary_condition",
            "allergies",
            "must_change_password",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        group_name = self.context["group_name"]
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.must_change_password = True

        if group_name == DOCTOR_GROUP and not user.doctor_id:
            user.doctor_id = generate_identifier("D", "doctor_id")
        if group_name == PATIENT_GROUP and not user.patient_id:
            user.patient_id = generate_identifier("P", "patient_id")

        user.save()
        set_user_group(user, group_name)
        return user


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=[ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP],
        required=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "electronic_signature",
            "patient_id",
            "doctor_id",
            "specialization",
            "age",
            "gender",
            "blood_type",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "primary_condition",
            "allergies",
            "must_change_password",
            "role",
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        group_name = validated_data.pop("role", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            validate_password(password, instance)
            instance.set_password(password)
            instance.must_change_password = True
        instance.save()
        if group_name:
            set_user_group(instance, group_name)
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
