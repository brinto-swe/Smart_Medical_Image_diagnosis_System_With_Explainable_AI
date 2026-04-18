from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP, User
from .utils import generate_identifier, set_user_group


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    dashboard = serializers.CharField(read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    electronic_signature_url = serializers.SerializerMethodField()

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


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.patient_id = generate_identifier("P", "patient_id")
        user.save(update_fields=["password", "patient_id"])
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
