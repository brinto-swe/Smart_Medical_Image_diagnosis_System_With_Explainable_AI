from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "MediCare profile",
            {
                "fields": (
                    "profile_picture",
                    "electronic_signature",
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
                )
            },
        ),
    )
    list_display = ("id", "username", "email", "first_name", "last_name", "role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name", "patient_id", "doctor_id")
