from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator
from .validators import PermissiveUsernameValidator, ReservedUsernameValidator


# ═══════════════════════════════════════════════════════════
# USER PERSONNALISÉ
# ═══════════════════════════════════════════════════════════
class User(AbstractUser):
    """
    Modèle utilisateur d'Armpad.
    Étend AbstractUser avec : username permissif, avatar, bio, langue, thème,
    et vérification d'email.
    """

    # ─── Pseudo permissif (emojis, accents, caractères spéciaux) ───
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            MinLengthValidator(3, message="Le pseudo doit contenir au moins 3 caractères."),
            PermissiveUsernameValidator(),
            ReservedUsernameValidator(),
        ],
        error_messages={
            'unique': "Ce pseudo est déjà pris.",
            'blank': "Le pseudo est obligatoire.",
        },
        verbose_name="Pseudo",
    )

    # ─── Profil ───
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Photo de profil"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Biographie"
    )

    # ─── Email unique (pour la connexion par email) ───
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email"
    )

    # ═══════════════════════════════════════════════════════════
    # VÉRIFICATION EMAIL
    # ═══════════════════════════════════════════════════════════
    email_verified = models.BooleanField(
        default=False,
        verbose_name="Email vérifié"
    )
    email_verification_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Token de vérification"
    )
    email_verification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernier envoi de vérification"
    )

    # ─── Préférences ───
    LANGUAGES = [
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
        ('de', 'Deutsch'),
    ]
    preferred_language = models.CharField(
        max_length=10,
        choices=LANGUAGES,
        default='fr',
        verbose_name="Langue préférée"
    )

    THEMES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
    ]
    theme = models.CharField(
        max_length=10,
        choices=THEMES,
        default='light',
        verbose_name="Thème"
    )

    # ─── Compteurs (dénormalisés pour performance) ───
    followers_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Abonnés"
    )
    following_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Abonnements"
    )

    # ─── Métadonnées ───
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.username

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None

    @property
    def initial(self):
        return self.username[0].upper() if self.username else '?'


# ═══════════════════════════════════════════════════════════
# FOLLOW (abonnements entre utilisateurs)
# ═══════════════════════════════════════════════════════════
class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    followed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"

    def __str__(self):
        return f"{self.follower.username} → {self.followed.username}"


# ═══════════════════════════════════════════════════════════
# MESSAGE (chat privé)
# ═══════════════════════════════════════════════════════════
class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}"


# ═══════════════════════════════════════════════════════════
# RÉACTION À UN MESSAGE
# ═══════════════════════════════════════════════════════════
class MessageReaction(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_reactions'
    )
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')
        verbose_name = "Réaction"
        verbose_name_plural = "Réactions"

    def __str__(self):
        return f"{self.user.username} → {self.emoji}"


# ═══════════════════════════════════════════════════════════
# NOTIFICATION
# ═══════════════════════════════════════════════════════════
class Notification(models.Model):
    """Notification pour l'utilisateur."""
    TYPE_CHOICES = [
        ('follow', 'Nouvel abonné'),
        ('like', 'Nouveau like'),
        ('comment', 'Nouveau commentaire'),
        ('chapter', 'Nouveau chapitre'),
        ('work', 'Nouvelle œuvre'),
        ('message', 'Nouveau message'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True,
        blank=True,
        verbose_name="Expéditeur"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Type"
    )
    message = models.CharField(max_length=300, verbose_name="Message")
    link = models.CharField(max_length=300, blank=True, verbose_name="Lien")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.user.username} - {self.message}"

    @property
    def icon(self):
        """Icône Font Awesome selon le type."""
        icons = {
            'follow': 'fa-user-plus',
            'like': 'fa-heart',
            'comment': 'fa-comment',
            'chapter': 'fa-book-open',
            'work': 'fa-book',
            'message': 'fa-envelope',
        }
        return icons.get(self.type, 'fa-bell')

    @property
    def color(self):
        """Couleur selon le type — palette rose/pastel du site."""
        colors = {
            'follow':    '#E8739A',
            'like':      '#C45580',
            'comment':   '#F4A7C0',
            'chapter':   '#BE185D',
            'work':      '#F7C5D5',
            'message':   '#9A808C',
        }
        return colors.get(self.type, '#E8739A')