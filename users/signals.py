import secrets
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

from .models import Follow, Notification

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# VÉRIFICATION EMAIL À L'INSCRIPTION
# ═══════════════════════════════════════════════════════════
@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    """Envoie un email de vérification à l'inscription."""
    if not created:
        return

    if not instance.email:
        return

    token = secrets.token_urlsafe(48)
    User.objects.filter(pk=instance.pk).update(
        email_verification_token=token,
        email_verification_sent_at=timezone.now()
    )

    site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    verification_url = f"{site_url}/verify-email/{token}/"

    subject = "Armpad — Confirmez votre adresse email"
    message = f"""Bonjour {instance.username},

Merci de vous être inscrit sur Armpad !

Pour activer votre compte, cliquez sur le lien ci-dessous :

{verification_url}

Ce lien est valable 7 jours.

Si vous n'avez pas créé de compte, ignorez cet email.

Cordialement,
L'équipe Armpad
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"❌ Erreur envoi email à {instance.email} : {e}")


# ═══════════════════════════════════════════════════════════
# NOTIF : Nouvel abonné
# ═══════════════════════════════════════════════════════════
@receiver(post_save, sender=Follow)
def notify_new_follower(sender, instance, created, **kwargs):
    if not created:
        return
    Notification.objects.create(
        user=instance.followed,
        sender=instance.follower,
        type='follow',
        message=f"{instance.follower.username} s'est abonné à votre profil",
        link=f"/profil/{instance.follower.username}/"
    )


# ═══════════════════════════════════════════════════════════
# NOTIF : Nouveau like
# ═══════════════════════════════════════════════════════════
@receiver(post_save, sender='works.Like')
def notify_new_like(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.work:
        work = instance.work
        if work.author != instance.user:
            Notification.objects.create(
                user=work.author,
                sender=instance.user,
                type='like',
                message=f"{instance.user.username} a aimé votre œuvre « {work.title} »",
                link=f"/oeuvre/{work.pk}/"
            )
    elif instance.chapter:
        chapter = instance.chapter
        if chapter.work.author != instance.user:
            Notification.objects.create(
                user=chapter.work.author,
                sender=instance.user,
                type='like',
                message=f"{instance.user.username} a aimé votre chapitre « {chapter.title} »",
                link=f"/oeuvre/{chapter.work.pk}/chapitre/{chapter.order}/"
            )
    elif instance.comment:
        comment = instance.comment
        if comment.user != instance.user:
            Notification.objects.create(
                user=comment.user,
                sender=instance.user,
                type='like',
                message=f"{instance.user.username} a aimé votre commentaire",
                link=''
            )


# ═══════════════════════════════════════════════════════════
# NOTIF : Nouveau chapitre publié
# ═══════════════════════════════════════════════════════════
@receiver(post_save, sender='works.Chapter')
def notify_new_chapter(sender, instance, created, **kwargs):
    if not created or instance.is_draft:
        return

    from works.models import Library
    work = instance.work
    for item in Library.objects.filter(work=work).select_related('user'):
        if item.user != work.author:
            Notification.objects.create(
                user=item.user,
                sender=work.author,
                type='chapter',
                message=f"Nouveau chapitre dans « {work.title} » : {instance.title}",
                link=f"/oeuvre/{work.pk}/chapitre/{instance.order}/"
            )


# ═══════════════════════════════════════════════════════════
# NOTIF : Nouvelle œuvre publiée
# ═══════════════════════════════════════════════════════════
@receiver(post_save, sender='works.Work')
def notify_new_work(sender, instance, created, **kwargs):
    if not created or instance.status == 'draft':
        return

    author = instance.author
    for follow in Follow.objects.filter(followed=author).select_related('follower'):
        Notification.objects.create(
            user=follow.follower,
            sender=author,
            type='work',
            message=f"{author.username} a publié une nouvelle œuvre : « {instance.title} »",
            link=f"/oeuvre/{instance.pk}/"
        )