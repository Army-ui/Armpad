from django.urls import path
from . import views

urlpatterns = [
    path('plans/',    views.PlanListView.as_view(),              name='plan_list'),
    path('me/',       views.MySubscriptionView.as_view(),        name='my_subscription'),
    path('checkout/', views.CreateCheckoutSessionView.as_view(), name='checkout'),
    path('webhook/',  views.StripeWebhookView.as_view(),         name='stripe_webhook'),
    path('payments/', views.PaymentHistoryView.as_view(),        name='payment_history'),
]