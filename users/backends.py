from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend d'authentification SÉCURISÉ.
    - Vérifie que l'email existe (case-insensitive)
    - Vérifie que le mot de passe correspond au hash stocké
    - Ne révèle jamais si l'email existe ou non (sécurité)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Récupérer l'identifiant (email OU username)
        identifier = username or kwargs.get('email')

        if identifier is None or password is None:
            return None

        try:
            # Recherche STRICTE par email (case-insensitive)
            user = User.objects.get(email__iexact=identifier.strip())
        except User.DoesNotExist:
            # Fallback : essayer par username
            try:
                user = User.objects.get(username__iexact=identifier.strip())
            except User.DoesNotExist:
                # ⚠️ On lance quand même un hash check pour éviter le timing attack
                User().set_password(password)
                return None
            except User.MultipleObjectsReturned:
                return None
        except User.MultipleObjectsReturned:
            # Plusieurs comptes avec le même email (ne devrait pas arriver)
            return None

        # ═══ VÉRIFICATION DU MOT DE PASSE ═══
        # check_password() utilise le hash + sel, c'est la méthode sécurisée
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None