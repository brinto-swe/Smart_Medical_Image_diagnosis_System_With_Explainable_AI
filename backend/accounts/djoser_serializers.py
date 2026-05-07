from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from rest_framework import serializers

from .models import PATIENT_GROUP, User
from .utils import generate_identifier, set_user_group


class PatientSignupSerializer(DjoserUserCreateSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    age = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "age", "phone_number"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        email = (attrs.get("email") or "").strip()
        if not email:
            raise serializers.ValidationError({"email": "Email is required."})
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        attrs["email"] = email
        if not (attrs.get("username") or "").strip():
            attrs["username"] = self._username_from_email(email)
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
        user = super().perform_create(validated_data)
        if not user.patient_id:
            user.patient_id = generate_identifier("P", "patient_id")
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.age = validated_data.get("age", user.age)
        user.phone_number = validated_data.get("phone_number", user.phone_number)
        user.save(update_fields=["is_active", "patient_id", "first_name", "last_name", "age", "phone_number"])
        set_user_group(user, PATIENT_GROUP)
        return user
