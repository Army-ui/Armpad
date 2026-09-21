from django.apps import AppConfig


class WorksConfig(AppConfig):
    name = 'works'

class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'
    verbose_name = 'Abonnements'