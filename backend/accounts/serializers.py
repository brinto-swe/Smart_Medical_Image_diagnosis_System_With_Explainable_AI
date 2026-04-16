from rest_framework import serializers
from .models import User


class DoctorCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'full_name', 'specialization']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role='doctor',
            full_name=validated_data.get('full_name', ''),
            specialization=validated_data.get('specialization', '')
        )
        return user