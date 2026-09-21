from rest_framework import permissions
from django.utils import timezone
from subscriptions.models import Subscription

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'work') and hasattr(obj.work, 'author'):
            return obj.work.author == request.user
        return False

class IsAuthorOfWork(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'work'):
            return obj.work.author == request.user
        return False

class HasPremiumAccess(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        is_premium = getattr(obj, 'is_premium', False)
        if not is_premium:
            return True
        user = request.user
        if user.is_staff:
            return True
        if hasattr(obj, 'author') and obj.author == user:
            return True
        if hasattr(obj, 'work') and obj.work.author == user:
            return True
        now = timezone.now()
        return Subscription.objects.filter(user=user, is_active=True, end_date__gt=now).exists()

# ✅ NOUVEAU – utilisé dans tes vues
class IsPremiumOrFreeContent(permissions.BasePermission):
    """
    Autorise l'accès si le contenu est gratuit, ou si l'utilisateur est Premium / auteur / staff.
    """
    def has_object_permission(self, request, view, obj):
        # Si l'objet n'est pas Premium, tout le monde peut y accéder
        is_premium = getattr(obj, 'is_premium', False)
        if not is_premium:
            return True
        # Si l'objet est Premium, vérifier les droits
        user = request.user
        if user.is_staff:
            return True
        if hasattr(obj, 'author') and obj.author == user:
            return True
        if hasattr(obj, 'work') and obj.work.author == user:
            return True
        # Vérifier l'abonnement Premium de l'utilisateur
        now = timezone.now()
        return Subscription.objects.filter(user=user, is_active=True, end_date__gt=now).exists()