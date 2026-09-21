from django import forms
from django.forms import inlineformset_factory
from .models import Work, Chapter, ChapterImage, Genre


# ═══════════════════════════════════════════════════════════
# FORMULAIRE D'ŒUVRE
# ═══════════════════════════════════════════════════════════
class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = [
            'title', 'summary', 'cover', 'genre',
            'language', 'status', 'is_premium', 'tags',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Titre de votre œuvre"
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': "Résumé de votre œuvre..."
            }),
            'cover': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'genre': forms.Select(attrs={
                'class': 'form-control'
            }),
            'language': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_premium': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "fantasy, romance, aventure (séparés par des virgules)"
            }),
        }
        labels = {
            'title': "Titre de l'œuvre",
            'summary': "Résumé",
            'cover': "Couverture",
            'genre': "Genre principal",
            'language': "Langue",
            'status': "Statut de publication",
            'is_premium': "Contenu Premium",
            'tags': "Mots-clés",
        }
        help_texts = {
            'cover': "Format recommandé : 400x600 px (ratio 2:3)",
            'tags': "Séparez les mots-clés par des virgules",
            'status': "Choisissez « En cours » ou « Terminé » pour publier dans le catalogue.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ne rendre le champ genre obligatoire que s'il y a des genres disponibles
        if not Genre.objects.exists():
            self.fields['genre'].required = False

    def clean_tags(self):
        """Nettoie la liste des tags."""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            cleaned = ', '.join([t.strip() for t in tags.split(',') if t.strip()])
            return cleaned
        return tags


# ═══════════════════════════════════════════════════════════
# FORMULAIRE DE CHAPITRE
# ═══════════════════════════════════════════════════════════
class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['title', 'content', 'image', 'is_draft', 'is_premium']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Titre du chapitre"
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': "Écrivez le contenu texte du chapitre (optionnel si vous utilisez des images)..."
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'is_draft': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_premium': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': "Titre du chapitre",
            'content': "Contenu texte",
            'image': "Image de couverture du chapitre",
            'is_draft': "Garder en brouillon",
            'is_premium': "Réservé aux Premium",
        }
        help_texts = {
            'image': "Cette image apparaîtra comme miniature du chapitre.",
            'is_draft': "Cochez pour garder le chapitre privé (invisible pour les lecteurs).",
        }


# ═══════════════════════════════════════════════════════════
# FORMSET POUR LES IMAGES (style Webtoon)
# ═══════════════════════════════════════════════════════════
ChapterImageFormSet = inlineformset_factory(
    Chapter,
    ChapterImage,
    fields=['image', 'caption', 'order'],
    extra=3,
    can_delete=True,
    widgets={
        'image': forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        'caption': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Légende (optionnel)"
        }),
        'order': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        }),
    }
)