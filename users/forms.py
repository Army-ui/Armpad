from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# INSCRIPTION
# ═══════════════════════════════════════════════════════════
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'vous@email.com',
            'autocomplete': 'email',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'preferred_language']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': "Pseudo (emojis autorisés ✨)",
                'autocomplete': 'username',
            })
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            })
        if 'preferred_language' in self.fields:
            self.fields['preferred_language'].widget.attrs.update({
                'class': 'form-control'
            })

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("L'email est obligatoire.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Le pseudo est obligatoire.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Ce pseudo est déjà pris.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        if commit:
            user.save()
        return user


# ═══════════════════════════════════════════════════════════
# CONNEXION
# ═══════════════════════════════════════════════════════════
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'vous@email.com',
            'autocomplete': 'email',
            'autofocus': True,
        })
    )

    error_messages = {
        'invalid_login': "Email ou mot de passe incorrect.",
        'inactive': "Ce compte est désactivé.",
    }

    def clean_username(self):
        return self.cleaned_data.get('username', '').strip().lower()


# ═══════════════════════════════════════════════════════════
# MOT DE PASSE OUBLIÉ
# ═══════════════════════════════════════════════════════════
from django.contrib.auth.forms import PasswordResetForm

class PasswordResetRequestForm(PasswordResetForm):
    """
    Formulaire de demande de réinitialisation.
    Hérite de PasswordResetForm pour bénéficier de la méthode save() qui envoie l'email.
    """
    email = forms.EmailField(
        label="Votre adresse email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'vous@email.com',
            'autocomplete': 'email',
            'autofocus': True,
        })
    )

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()


# ═══════════════════════════════════════════════════════════
# NOUVEAU MOT DE PASSE
# ═══════════════════════════════════════════════════════════
from django.contrib.auth.forms import SetPasswordForm


class StyledSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'autofocus': True,
        })
    )
    new_password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        })
    )


# ═══════════════════════════════════════════════════════════
# ÉDITION DE PROFIL
# ═══════════════════════════════════════════════════════════
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'bio', 'avatar', 'preferred_language']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'preferred_language': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Cet email est déjà utilisé par un autre compte.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ce pseudo est déjà pris.")
        return username
    
from django import forms
from django.core.validators import EmailValidator

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        validators=[EmailValidator()],  # Validateur standard RFC 5322
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'vous@email.com',
            'autocomplete': 'email',
        })
    )    