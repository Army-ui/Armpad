from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Plan, Subscription, Payment


class PlanSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ('id', 'name', 'price', 'currency', 'interval',
                  'stripe_price_id', 'features')

    def get_name(self, obj):
        request = self.context.get('request')
        lang = getattr(request, 'LANGUAGE_CODE', 'fr') if request else 'fr'
        return obj.name_en if lang.startswith('en') else obj.name_fr

    def get_features(self, obj):
        request = self.context.get('request')
        lang = getattr(request, 'LANGUAGE_CODE', 'fr') if request else 'fr'
        return obj.features_en if lang.startswith('en') else obj.features_fr


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = ('id', 'plan', 'status', 'is_active',
                  'current_period_start', 'current_period_end',
                  'canceled_at', 'created_at')
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'amount', 'currency', 'status', 'created_at')
        read_only_fields = fields