from rest_framework.permissions import BasePermission

from accounts.models import ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP
from accounts.utils import user_has_group


class IsAdminUserGroup(BasePermission):
    def has_permission(self, request, view):
        return user_has_group(request.user, ADMIN_GROUP)


class IsDoctorUserGroup(BasePermission):
    def has_permission(self, request, view):
        return user_has_group(request.user, DOCTOR_GROUP)


class IsPatientUserGroup(BasePermission):
    def has_permission(self, request, view):
        return user_has_group(request.user, PATIENT_GROUP)


class IsAdminOrDoctor(BasePermission):
    def has_permission(self, request, view):
        return user_has_group(request.user, ADMIN_GROUP) or user_has_group(request.user, DOCTOR_GROUP)


class IsAdminDoctorOrPatient(BasePermission):
    def has_permission(self, request, view):
        return (
            user_has_group(request.user, ADMIN_GROUP)
            or user_has_group(request.user, DOCTOR_GROUP)
            or user_has_group(request.user, PATIENT_GROUP)
        )


# Backward-compatible aliases for old imports.
IsAdmin = IsAdminUserGroup
IsDoctor = IsDoctorUserGroup
