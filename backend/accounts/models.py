from django.contrib.auth.models import AbstractUser
from django.db import models


ADMIN_GROUP = "Admin"
DOCTOR_GROUP = "Doctor"
PATIENT_GROUP = "Patient"
ROLE_GROUPS = (ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP)


def user_profile_picture_path(instance, filename):
    return f"profile_pictures/user_{instance.pk or 'new'}/{filename}"


def user_signature_path(instance, filename):
    return f"signatures/user_{instance.pk or 'new'}/{filename}"


class User(AbstractUser):
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path,
        blank=True,
        null=True,
    )
    electronic_signature = models.ImageField(
        upload_to=user_signature_path,
        blank=True,
        null=True,
    )
    phone_number = models.CharField(max_length=30, blank=True)

    patient_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    doctor_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True)

    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True)
    blood_type = models.CharField(max_length=10, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    primary_condition = models.CharField(max_length=150, blank=True)
    allergies = models.CharField(max_length=255, blank=True)

    must_change_password = models.BooleanField(default=False)

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    @property
    def role(self):
        if self.is_superuser:
            return "admin"

        group = self.groups.filter(name__in=ROLE_GROUPS).first()
        return group.name.lower() if group else ""

    @property
    def dashboard(self):
        role = self.role
        if role == "admin":
            return "admin"
        if role == "doctor":
            return "doctor"
        return "patient"
