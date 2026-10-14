# regen_slugs.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'armpad.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("=== Utilisateurs AVANT ===")
for u in User.objects.all():
    print(f"  {u.username!r} -> slug = {u.slug!r}")

print("\n=== Régénération des slugs ===")
for u in User.objects.all():
    u.regenerate_slug(save=True)
    print(f"  {u.username!r} -> slug = {u.slug!r}")

print("\n✅ Slugs régénérés !")
