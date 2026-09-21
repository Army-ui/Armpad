from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from users.models import User


# ═══════════════════════════════════════════════════════════
# INSCRIPTION
# ═══════════════════════════════════════════════════════════
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'preferred_language']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Nom d'utilisateur"
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'vous@email.com'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'username': "Nom d'utilisateur",
            'email': "Adresse email",
            'preferred_language': "Langue préférée",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': '••••••••'
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': '••••••••'
            })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email


# ═══════════════════════════════════════════════════════════
# CONNEXION (par email OU username)
# ═══════════════════════════════════════════════════════════
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'vous@email.com',
            'autofocus': True,
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError("Email ou mot de passe incorrect.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("Ce compte est désactivé.")

        return self.cleaned_data


# Alias pour compatibilité (au cas où vous utilisez encore StyledAuthenticationForm)
StyledAuthenticationForm = EmailAuthenticationForm


# ═══════════════════════════════════════════════════════════
# ÉDITION DE PROFIL
# ═══════════════════════════════════════════════════════════
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'bio', 'avatar', 'preferred_language']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Nom d'utilisateur"
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'vous@email.com'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': "Parlez-nous de vous..."
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'username': "Nom d'utilisateur",
            'email': "Adresse email",
            'bio': "Biographie",
            'avatar': "Photo de profil",
            'preferred_language': "Langue préférée",
        }