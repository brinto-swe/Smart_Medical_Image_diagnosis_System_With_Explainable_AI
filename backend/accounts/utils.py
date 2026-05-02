from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP, ROLE_GROUPS


def ensure_role_groups():
    for group_name in ROLE_GROUPS:
        Group.objects.get_or_create(name=group_name)


def set_user_group(user, group_name):
    ensure_role_groups()
    user.groups.set([Group.objects.get(name=group_name)])


def user_has_group(user, group_name):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser and group_name == ADMIN_GROUP:
        return True
    return user.groups.filter(name=group_name).exists()


def generate_identifier(prefix, field_name):
    User = get_user_model()
    latest = (
        User.objects.filter(**{f"{field_name}__startswith": prefix})
        .order_by(f"-{field_name}")
        .values_list(field_name, flat=True)
        .first()
    )
    if latest:
        try:
            number = int(latest.replace(prefix, "")) + 1
        except ValueError:
            number = User.objects.filter(**{f"{field_name}__startswith": prefix}).count() + 1
    else:
        number = 1
    return f"{prefix}{number:03d}"


def ensure_user_role_identifier(user):
    update_fields = []
    if user.groups.filter(name=DOCTOR_GROUP).exists() and not user.doctor_id:
        user.doctor_id = generate_identifier("D", "doctor_id")
        update_fields.append("doctor_id")
    if user.groups.filter(name=PATIENT_GROUP).exists() and not user.patient_id:
        user.patient_id = generate_identifier("P", "patient_id")
        update_fields.append("patient_id")
    if update_fields:
        user.save(update_fields=update_fields)
    return user


def ensure_group_identifiers(group_name):
    User = get_user_model()
    ensure_role_groups()
    if group_name == DOCTOR_GROUP:
        users = User.objects.filter(groups__name=DOCTOR_GROUP, doctor_id__isnull=True)
        users = list(users) + list(User.objects.filter(groups__name=DOCTOR_GROUP, doctor_id=""))
    elif group_name == PATIENT_GROUP:
        users = User.objects.filter(groups__name=PATIENT_GROUP, patient_id__isnull=True)
        users = list(users) + list(User.objects.filter(groups__name=PATIENT_GROUP, patient_id=""))
    else:
        users = []
    seen = set()
    for user in users:
        if user.pk in seen:
            continue
        seen.add(user.pk)
        ensure_user_role_identifier(user)
