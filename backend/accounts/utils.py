from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import ADMIN_GROUP, ROLE_GROUPS


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
