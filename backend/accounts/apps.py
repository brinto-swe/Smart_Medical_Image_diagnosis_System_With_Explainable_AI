from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from django.db.models.signals import post_migrate

        def create_role_groups(sender, **kwargs):
            from .utils import ensure_role_groups

            ensure_role_groups()

        post_migrate.connect(create_role_groups, sender=self)
