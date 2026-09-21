import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PermissiveUsernameValidator:
    """
    Validateur de pseudo permissif.
    Autorise : lettres (toutes langues), chiffres, emojis,
    espaces, points, tirets, underscores, +, @.
    Interdit : les caractères vraiment problématiques pour les URLs / HTML.
    """
    # Caractères INTERDITS (tout le reste est autorisé)
    forbidden = re.compile(
        r'[<>"\'`\\/;:!?*&^%$#(){}\[\]|=~]'  # ponctuation dangereuse
        r'|[\x00-\x1f\x7f]'                   # caractères de contrôle
    )

    message = _(
        "Le pseudo ne peut pas contenir les caractères < > \" ' ` \\ / ; : ! ? "
        "ou d'autres symboles réservés."
    )
    code = 'invalid_username'

    def __call__(self, value):
        if not value:
            return
        if self.forbidden.search(value):
            raise ValidationError(self.message, code=self.code, params={'value': value})

    def __eq__(self, other):
        return (
            isinstance(other, PermissiveUsernameValidator)
            and self.forbidden.pattern == other.forbidden.pattern
        )

    def __hash__(self):
        return hash(self.forbidden.pattern)

    def deconstruct(self):
        return (
            'users.validators.PermissiveUsernameValidator',
            [],
            {},
        )


class ReservedUsernameValidator:
    """Interdit certains pseudos réservés (admin, support, etc.)."""
    RESERVED = {
        'admin', 'administrator', 'root', 'system', 'support',
        'moderator', 'mod', 'armpad', 'staff', 'official',
        'help', 'contact', 'about', 'api', 'www', 'mail',
    }
    message = _("Ce pseudo est réservé et ne peut pas être utilisé.")
    code = 'reserved_username'

    def __call__(self, value):
        if value and value.lower().strip() in self.RESERVED:
            raise ValidationError(self.message, code=self.code, params={'value': value})

    def __eq__(self, other):
        return isinstance(other, ReservedUsernameValidator)

    def __hash__(self):
        return hash('ReservedUsernameValidator')

    def deconstruct(self):
        return (
            'users.validators.ReservedUsernameValidator',
            [],
            {},
        )