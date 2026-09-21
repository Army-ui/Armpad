from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# PATTERNS D'EMAILS DE TEST À SUPPRIMER
# ═══════════════════════════════════════════════════════════
TEST_EMAIL_DOMAINS = [
    '@example.com',
    '@example.org',
    '@test.com',
    '@test.fr',
    '@localhost',
    '@mail.com',
    '@tempmail.com',
    '@fake.com',
    '@fake.org',
    '@yopmail.com',
]

TEST_USERNAME_PATTERNS = [
    'test',
    'demo',
    'fake',
    'toto',
    'tata',
    'tutu',
    'abc',
    'xyz',
    'aaa',
    'bbb',
    'utilisateur',
    'user',
    'admin_test',
]


class Command(BaseCommand):
    help = "Supprime les comptes de test (emails/username factices)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Affiche ce qui sera supprimé SANS rien supprimer",
        )
        parser.add_argument(
            '--inactive-only',
            action='store_true',
            help="Ne supprime que les comptes jamais connectés (last_login is null)",
        )
        parser.add_argument(
            '--no-superuser',
            action='store_true',
            help="Ne touche pas aux superusers (par défaut, ils sont protégés)",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        inactive_only = options['inactive_only']

        self.stdout.write(self.style.WARNING(
            "\n🧹 Nettoyage des comptes de test...\n"
        ))

        # ═══ Construire la requête ═══
        email_filter = Q()
        for domain in TEST_EMAIL_DOMAINS:
            email_filter |= Q(email__iendswith=domain)

        username_filter = Q()
        for pattern in TEST_USERNAME_PATTERNS:
            username_filter |= Q(username__iexact=pattern)
            username_filter |= Q(username__istartswith=pattern + '_')
            username_filter |= Q(username__istartswith=pattern + '.')

        users = User.objects.filter(email_filter | username_filter)

        # Protéger les superusers
        if options.get('no_superuser', True):
            users = users.exclude(is_superuser=True)

        # Filtrer les jamais connectés
        if inactive_only:
            users = users.filter(last_login__isnull=True)

        users = users.distinct()

        count = users.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                "✅ Aucun compte de test trouvé. Rien à faire.\n"
            ))
            return

        # ═══ Afficher ce qui sera supprimé ═══
        self.stdout.write(f"📋 {count} compte(s) trouvé(s) :\n")

        for user in users:
            marker = "🧪" if any(user.email.endswith(d) for d in TEST_EMAIL_DOMAINS) else "👤"
            self.stdout.write(
                f"  {marker} ID {user.pk} | {user.username} | {user.email} | "
                f"last_login: {user.last_login or 'jamais'} | superuser: {user.is_superuser}"
            )

        # ═══ Mode dry-run ═══
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  MODE DRY-RUN : rien n'a été supprimé."
            ))
            self.stdout.write(
                f"Pour supprimer réellement, relancez sans --dry-run :\n"
                f"  python manage.py clean_test_users\n"
            )
            return

        # ═══ Confirmation ═══
        self.stdout.write("")
        confirm = input(
            f"⚠️  Supprimer définitivement {count} compte(s) ? (oui/non) : "
        )
        if confirm.lower() not in ('oui', 'o', 'yes', 'y'):
            self.stdout.write(self.style.WARNING("❌ Annulé. Aucune suppression.\n"))
            return

        # ═══ Suppression ═══
        deleted_count = 0
        for user in users:
            username = user.username
            user.delete()
            deleted_count += 1
            self.stdout.write(f"  🗑️  Supprimé : {username}")

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ {deleted_count} compte(s) supprimé(s).\n"
        ))