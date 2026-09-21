# permissions.py
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


def get_owner(obj):
    """
    Récupère l'utilisateur propriétaire d'un objet de manière générique.
    - Si l'objet a un champ 'author', on le retourne.
    - Sinon, s'il a un champ 'user', on le retourne.
    - Sinon, s'il a un champ 'work', on appelle récursivement sur obj.work.
    - Enfin, si le propriétaire trouvé est un Profile (ou un modèle avec un champ 'user'),
      on retourne son utilisateur associé pour une comparaison fiable avec request.user.
    """
    owner = None
    if hasattr(obj, 'author'):
        owner = obj.author
    elif hasattr(obj, 'user'):
        owner = obj.user
    elif hasattr(obj, 'work'):
        owner = get_owner(obj.work)  # remonte à l'œuvre parente

    # Si le propriétaire est un modèle Profile (ou similaire) avec un champ 'user',
    # on extrait l'utilisateur Django sous-jacent.
    if owner and hasattr(owner, 'user'):
        owner = owner.user

    return owner


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Lecture libre, modification uniquement par l'auteur.
    Compatible avec les objets qui n'ont pas directement 'author' (ex: Chapter).
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = get_owner(obj)
        return owner == request.user


class IsPremiumOrFreeContent(permissions.BasePermission):
    """
    Règles Premium :
    - Contenu gratuit → accessible à tous
    - Contenu premium + non connecté → refusé
    - Contenu premium + connecté non premium → refusé
    - Contenu premium + abonné premium → autorisé
    - Contenu premium + staff/admin → autorisé
    - Auteur de l'œuvre → toujours autorisé
    """
    message = _("Ce contenu est réservé aux abonnés Premium.")

    def has_object_permission(self, request, view, obj):
        # Contenu gratuit → tout le monde
        if not obj.is_premium:
            return True

        # Non connecté → refusé
        if not request.user.is_authenticated:
            return False

        # L'auteur peut toujours accéder à son propre contenu
        author = get_owner(obj)
        if author and author == request.user:
            return True

        # Staff/admin → autorisé
        if request.user.is_staff:
            return True

        # Vérifier l'abonnement actif
        return self._is_premium_active(request.user)

    def _is_premium_active(self, user):
        """Vérifie que l'abonnement est vraiment actif et non expiré."""
        if not user.is_premium:
            return False
        # Double vérification via la table subscription
        try:
            sub = user.subscription
            return sub.is_active
        except Exception:
            # Pas de subscription en base mais is_premium=True → on fait confiance
            return user.is_premium


class IsOwnerOnly(permissions.BasePermission):
    """Accès uniquement au propriétaire de l'objet."""
    def has_object_permission(self, request, view, obj):
        owner = get_owner(obj)
        return owner == request.user


class IsAuthor(permissions.BasePermission):
    """Vérifie que l'utilisateur est l'auteur — pour les actions d'écriture."""
    def has_object_permission(self, request, view, obj):
        owner = get_owner(obj)
        return owner == request.user