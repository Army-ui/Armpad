import stripe
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from .models import Plan, Subscription, Payment
from .serializers import PlanSerializer, SubscriptionSerializer, PaymentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class PlanListView(generics.ListAPIView):
    """GET /api/v1/subscriptions/plans/ — Tous les plans premium."""
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class MySubscriptionView(generics.RetrieveAPIView):
    """GET /api/v1/subscriptions/me/ — Mon abonnement actuel."""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return getattr(self.request.user, 'subscription', None)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response(
                {"message": _("Aucun abonnement actif."), "is_premium": False}
            )
        return Response(SubscriptionSerializer(instance, context={'request': request}).data)


class CreateCheckoutSessionView(APIView):
    """
    POST /api/v1/subscriptions/checkout/
    Crée une session Stripe Checkout et retourne l'URL de paiement.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        try:
            plan = Plan.objects.get(pk=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response(
                {"error": _("Plan introuvable.")},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            session = stripe.checkout.Session.create(
                customer_email=request.user.email,
                payment_method_types=['card'],
                line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
                mode='subscription',
                success_url=f"{request.scheme}://{request.get_host()}/premium/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{request.scheme}://{request.get_host()}/premium/cancel",
                metadata={'user_id': str(request.user.id), 'plan_id': str(plan.id)},
            )
            return Response({'checkout_url': session.url})
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripeWebhookView(APIView):
    """
    POST /api/v1/subscriptions/webhook/
    Reçoit les événements Stripe (paiement réussi, annulation…).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event['type'] == 'checkout.session.completed':
            self._handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            self._handle_subscription_canceled(event['data']['object'])

        return Response({'status': 'ok'})

    def _handle_checkout_completed(self, session):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_id = session['metadata'].get('user_id')
        plan_id = session['metadata'].get('plan_id')
        try:
            user = User.objects.get(pk=user_id)
            plan = Plan.objects.get(pk=plan_id)
            sub_data = stripe.Subscription.retrieve(session['subscription'])
            sub, _ = Subscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'status': 'active',
                    'stripe_subscription_id': sub_data['id'],
                    'stripe_customer_id': sub_data['customer'],
                    'current_period_start': timezone.datetime.fromtimestamp(
                        sub_data['current_period_start'], tz=timezone.utc),
                    'current_period_end': timezone.datetime.fromtimestamp(
                        sub_data['current_period_end'], tz=timezone.utc),
                }
            )
            user.is_premium = True
            user.save(update_fields=['is_premium'])
        except Exception:
            pass

    def _handle_subscription_canceled(self, stripe_sub):
        try:
            sub = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
            sub.status = 'canceled'
            sub.canceled_at = timezone.now()
            sub.save()
            sub.user.is_premium = False
            sub.user.save(update_fields=['is_premium'])
        except Subscription.DoesNotExist:
            pass


class PaymentHistoryView(generics.ListAPIView):
    """GET /api/v1/subscriptions/payments/ — Historique de mes paiements."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(
            subscription__user=self.request.user
        ).order_by('-created_at')