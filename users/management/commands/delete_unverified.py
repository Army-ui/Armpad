from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Supprime les comptes non vérifiés depuis plus de X jours"

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help="Nombre de jours avant suppression")
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timedelta(days=days)
        
        # Non vérifiés + créés il y a plus de X jours
        users = User.objects.filter(
            email_verified=False,
            date_joined__lt=cutoff,
        ).exclude(is_superuser=True)
        
        count = users.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"✅ Aucun compte non vérifié de plus de {days} jours."))
            return
        
        self.stdout.write(f"🗑️ {count} compte(s) non vérifiés depuis +{days} jours :\n")
        for u in users:
            self.stdout.write(f"  → {u.username} | {u.email} | inscrit {u.date_joined.strftime('%d/%m/%Y')}")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("\n⚠️ Mode DRY-RUN."))
            return
        
        confirm = input(f"\nSupprimer ces {count} comptes ? (oui/non) : ")
        if confirm.lower() != 'oui':
            self.stdout.write("❌ Annulé.")
            return
        
        for u in users:
            u.delete()
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ {count} compte(s) supprimé(s)."))