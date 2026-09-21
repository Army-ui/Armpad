from django.urls import path
from django.contrib.auth import views as auth_views
from . import views as user_views
from .forms import (
    EmailAuthenticationForm,
    PasswordResetRequestForm,
    StyledSetPasswordForm,
)

app_name = 'users_web'

urlpatterns = [
    # ═══ LOGIN / LOGOUT ═══
    path('login/', auth_views.LoginView.as_view(
        template_name='armpad/login.html',
        authentication_form=EmailAuthenticationForm,
        redirect_authenticated_user=True,
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='web:home'
    ), name='logout'),

    # ═══ VÉRIFICATION EMAIL ═══
    path('verify-email/<str:token>/', user_views.verify_email, name='verify_email'),

    # ═══ MOT DE PASSE OUBLIÉ ═══
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='armpad/password_reset.html',
        email_template_name='armpad/emails/password_reset_email.txt',
        html_email_template_name='armpad/emails/password_reset_email.html',
        subject_template_name='armpad/emails/password_reset_subject.txt',
        form_class=PasswordResetRequestForm,
        success_url='/password-reset/done/',
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='armpad/password_reset_done.html',
    ), name='password_reset_done'),

    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='armpad/password_reset_confirm.html',
        form_class=StyledSetPasswordForm,
        success_url='/password-reset/complete/',
    ), name='password_reset_confirm'),

    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='armpad/password_reset_complete.html',
    ), name='password_reset_complete'),
]