import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Plan(models.Model):
    """Plans d'abonnement premium."""
    INTERVAL_CHOICES = [
        ('month', _('Mensuel')),
        ('year', _('Annuel')),
    ]

    name_fr = models.CharField(_('nom FR'), max_length=100)
    name_en = models.CharField(_('nom EN'), max_length=100)
    price = models.DecimalField(_('prix'), max_digits=8, decimal_places=2)
    currency = models.CharField(_('devise'), max_length=3, default='XAF')
    interval = models.CharField(
        _('fréquence'), max_length=10, choices=INTERVAL_CHOICES
    )
    stripe_price_id = models.CharField(
        _('Stripe Price ID'), max_length=100, blank=True
    )
    features_fr = models.JSONField(_('fonctionnalités FR'), default=list)
    features_en = models.JSONField(_('fonctionnalités EN'), default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'armpad_plans'

    def __str__(self):
        return f"{self.name_fr} — {self.price} {self.currency}/{self.interval}"


class Subscription(models.Model):
    """Abonnement premium d'un utilisateur."""

    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('canceled', _('Annulé')),
        ('expired', _('Expiré')),
        ('trialing', _('Essai')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='subscription', verbose_name=_('utilisateur')
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, verbose_name=_('plan')
    )
    status = models.CharField(
        _('statut'), max_length=20,
        choices=STATUS_CHOICES, default='active'
    )
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    current_period_start = models.DateTimeField(null=True)
    current_period_end = models.DateTimeField(null=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'armpad_subscriptions'
        verbose_name = _('abonnement')
        verbose_name_plural = _('abonnements')

    def __str__(self):
        return f"{self.user} — {self.plan} ({self.status})"

    @property
    def is_active(self):
        return self.status in ('active', 'trialing')


class Payment(models.Model):
    """Historique des paiements."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name='payments'
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default='XAF')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, default='succeeded')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'armpad_payments'
        ordering = ['-created_at']