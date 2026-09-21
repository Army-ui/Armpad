from django.core.management.base import BaseCommand
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from works.models import Genre


class Command(BaseCommand):
    help = 'Crée les genres par défaut dans la base de données'

    def handle(self, *args, **kwargs):
        genres = [
            ('Romance', 'Romance'),
            ('Dark Romance', 'Dark Romance'),
            ('Dark', 'Dark'),
            ('Fantasy', 'Fantasy'),
            ('Science Fiction', 'Science-Fiction'),
            ('Adventure', 'Aventure'),
            ('Mystery', 'Mystère'),
            ('Horror', 'Horreur'),
            ('Comedy', 'Comédie'),
            ('Drama', 'Drame'),
            ('Slice of Life', 'Tranche de vie'),
            ('Action', 'Action'),
            ('Historical', 'Historique'),
            ('Isekai', 'Isekai'),
            ('Fantastic', 'Fantastique'),
            ('Thriller', 'Thriller'),
            ('Detective', 'Policier'),
            ('Sports', 'Sport'),
            ('Shonen', 'Shonen'),
            ('Shojo', 'Shojo'),
            ('Seinen', 'Seinen'),
            ('Mecha', 'Mecha'),
        ]

        created_count = 0
        updated_count = 0

        for name_en, name_fr in genres:
            slug = slugify(name_en)
            obj, created = Genre.objects.get_or_create(
                slug=slug,
                defaults={
                    'name_en': name_en,
                    'name_fr': name_fr,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ {name_fr} ({name_en})'))
            else:
                # Mettre à jour si le genre existe déjà mais avec des noms différents
                changed = False
                if obj.name_en != name_en:
                    obj.name_en = name_en
                    changed = True
                if obj.name_fr != name_fr:
                    obj.name_fr = name_fr
                    changed = True
                if changed:
                    obj.save()
                    updated_count += 1
                    self.stdout.write(f'  ↻ {name_fr} (mis à jour)')
                else:
                    self.stdout.write(f'  · {name_fr} (déjà existant)')

        total = Genre.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n{created_count} créé(s), {updated_count} mis à jour. Total : {total}'
        ))