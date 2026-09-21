from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import models
import secrets

User = get_user_model()


class Command(BaseCommand):
    help = "Envoie un email de vérification à tous les comptes non vérifiés"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="Affiche sans envoyer")

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        users = User.objects.filter(email_verified=False).exclude(email='')
        count = users.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("✅ Tous les comptes sont déjà vérifiés."))
            return
        
        self.stdout.write(f"📧 {count} compte(s) à vérifier\n")
        
        for user in users:
            self.stdout.write(f"  → {user.email}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️ Mode DRY-RUN. Rien envoyé."))
            return
        
        confirm = input(f"\nEnvoyer {count} emails ? (oui/non) : ")
        if confirm.lower() != 'oui':
            self.stdout.write("❌ Annulé.")
            return
        
        sent = 0
        failed = 0
        for user in users:
            token = secrets.token_urlsafe(48)
            user.email_verification_token = token
            user.email_verification_sent_at = timezone.now()
            user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
            
            url = f"{settings.SITE_URL}/verify-email/{token}/"
            try:
                send_mail(
                    subject="Armpad — Confirmez votre email",
                    message=f"Bonjour {user.username},\n\nConfirmez votre email : {url}\n\nL'équipe Armpad",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                sent += 1
                self.stdout.write(f"  ✅ {user.email}")
            except Exception as e:
                failed += 1
                self.stdout.write(f"  ❌ {user.email} — {e}")
        
        self.stdout.write(self.style.SUCCESS(f"\n📊 {sent} envoyés, {failed} échecs"))