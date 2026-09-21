from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.db import models as django_models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from datetime import timedelta

from .serializers import (
    RegisterSerializer, UserPublicSerializer,
    UserPrivateSerializer, ChangePasswordSerializer
)
from .models import Follow, Notification, Message, MessageReaction
from .forms import (
    EmailAuthenticationForm,
    PasswordResetRequestForm,
    StyledSetPasswordForm,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════════
# AUTHENTIFICATION (API)
# ═══════════════════════════════════════════════════════════
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": _("Compte créé avec succès."), "user": UserPrivateSerializer(user).data},
            status=status.HTTP_201_CREATED
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPrivateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"detail": _("Ancien mot de passe incorrect.")}, status=400)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": _("Mot de passe mis à jour.")})


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'username'
    queryset = User.objects.all()


class FollowToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            return Response({"error": _("Vous ne pouvez pas vous suivre vous-même.")}, status=400)

        follow, created = Follow.objects.get_or_create(follower=request.user, followed=target)

        if not created:
            follow.delete()
            User.objects.filter(pk=target.pk).update(followers_count=django_models.F('followers_count') - 1)
            User.objects.filter(pk=request.user.pk).update(following_count=django_models.F('following_count') - 1)
            return Response({"following": False})

        User.objects.filter(pk=target.pk).update(followers_count=django_models.F('followers_count') + 1)
        User.objects.filter(pk=request.user.pk).update(following_count=django_models.F('following_count') + 1)
        return Response({"following": True}, status=201)


class SetThemeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        theme = request.data.get('theme')
        if theme not in ('light', 'dark'):
            return Response({"error": "Thème invalide."}, status=400)
        request.user.theme = theme
        request.user.save(update_fields=['theme'])
        return Response({"theme": theme})


class SetLanguageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        lang = request.data.get('language')
        if lang not in ('fr', 'en'):
            return Response({"error": "Langue invalide."}, status=400)
        request.user.preferred_language = lang
        request.user.save(update_fields=['preferred_language'])
        return Response({"language": lang})


# ═══════════════════════════════════════════════════════════
# NOTIFICATIONS (API)
# ═══════════════════════════════════════════════════════════
class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user)[:50]
        data = [{
            'id': n.id, 'type': n.type, 'message': n.message, 'link': n.link,
            'is_read': n.is_read, 'created_at': n.created_at.isoformat(),
            'sender': n.sender.username if n.sender else None,
        } for n in notifs]
        return Response(data)


class NotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
        return Response({'ok': True})


class NotificationReadAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'ok': True})


class NotificationUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'count': count})


# ═══════════════════════════════════════════════════════════
# CHAT (API)
# ═══════════════════════════════════════════════════════════
class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_other(self, username):
        return get_object_or_404(User, username=username)

    def get(self, request, username):
        other = self.get_other(username)
        msgs = Message.objects.filter(
            django_models.Q(sender=request.user, receiver=other) |
            django_models.Q(sender=other, receiver=request.user)
        ).order_by('created_at')[:200]

        Message.objects.filter(sender=other, receiver=request.user, is_read=False).update(is_read=True)

        data = [{
            'id': m.id, 'content': m.content, 'is_mine': m.sender == request.user,
            'created_at': m.created_at.isoformat(),
            'reactions': [{'emoji': r.emoji, 'user': r.user.username} for r in m.reactions.all()],
        } for m in msgs]
        return Response(data)

    def post(self, request, username):
        other = self.get_other(username)
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Message vide.'}, status=400)

        are_friends = (
            Follow.objects.filter(follower=request.user, followed=other).exists() and
            Follow.objects.filter(follower=other, followed=request.user).exists()
        )
        if not are_friends:
            return Response({'error': 'Vous devez être amis pour envoyer des messages.'}, status=403)

        msg = Message.objects.create(sender=request.user, receiver=other, content=content)

        Notification.objects.create(
            user=other, sender=request.user, type='message',
            message=f"{request.user.username} vous a envoyé un message",
            link=f"/chat/{request.user.username}/"
        )
        return Response({
            'id': msg.id, 'content': msg.content, 'is_mine': True,
            'created_at': msg.created_at.isoformat(), 'reactions': []
        }, status=201)


class ReactToMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        emoji = request.data.get('emoji', '').strip()
        if not emoji:
            return Response({'error': 'Emoji requis.'}, status=400)

        MessageReaction.objects.update_or_create(
            message=message, user=request.user,
            defaults={'emoji': emoji}
        )
        return Response({'status': 'ok', 'emoji': emoji})


# ═══════════════════════════════════════════════════════════
# FOLLOWERS / FOLLOWING (pages HTML)
# ═══════════════════════════════════════════════════════════
@login_required
def followers_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    follows = Follow.objects.filter(followed=profile_user).select_related('follower')

    users_data = []
    for f in follows:
        u = f.follower
        if u == request.user:
            continue
        is_following = Follow.objects.filter(follower=request.user, followed=u).exists()
        is_follower = True
        is_friend = is_following and is_follower
        users_data.append({
            'user': u,
            'is_following': is_following,
            'is_follower': is_follower,
            'is_friend': is_friend,
        })

    return render(request, 'armpad/user_list.html', {
        'profile_user': profile_user,
        'users_data': users_data,
        'title': f"Abonnés de {profile_user.username}",
        'active_tab': 'followers',
    })


@login_required
def following_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    follows = Follow.objects.filter(follower=profile_user).select_related('followed')

    users_data = []
    for f in follows:
        u = f.followed
        if u == request.user:
            continue
        is_following = True
        is_follower = Follow.objects.filter(follower=u, followed=request.user).exists()
        is_friend = is_following and is_follower
        users_data.append({
            'user': u,
            'is_following': is_following,
            'is_follower': is_follower,
            'is_friend': is_friend,
        })

    return render(request, 'armpad/user_list.html', {
        'profile_user': profile_user,
        'users_data': users_data,
        'title': f"Abonnements de {profile_user.username}",
        'active_tab': 'following',
    })


# ═══════════════════════════════════════════════════════════
# FOLLOW (AJAX)
# ═══════════════════════════════════════════════════════════
@login_required
@require_POST
def toggle_follow(request, username):
    """Suivre / Ne plus suivre un utilisateur (AJAX)."""
    target = get_object_or_404(User, username=username)

    if target == request.user:
        return JsonResponse({'error': 'Impossible de se suivre soi-même.'}, status=400)

    follow = Follow.objects.filter(follower=request.user, followed=target).first()

    if follow:
        follow.delete()
        target.followers_count = max(0, target.followers_count - 1)
        request.user.following_count = max(0, request.user.following_count - 1)
        is_following = False
    else:
        Follow.objects.create(follower=request.user, followed=target)
        target.followers_count += 1
        request.user.following_count += 1
        is_following = True

    target.save(update_fields=['followers_count'])
    request.user.save(update_fields=['following_count'])

    return JsonResponse({
        'status': 'ok',
        'is_following': is_following,
        'followers_count': target.followers_count
    })


# ═══════════════════════════════════════════════════════════
# NOTIFICATIONS (WEB — pages HTML)
# ═══════════════════════════════════════════════════════════
@login_required
def notifications_page(request):
    notifs = Notification.objects.filter(user=request.user).select_related('sender')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'armpad/notifications.html', {'notifications': notifs})


@login_required
@require_POST
def mark_notification_read(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


@login_required
def unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


# ═══════════════════════════════════════════════════════════
# MOT DE PASSE OUBLIÉ — personnalisation
# ═══════════════════════════════════════════════════════════
class CustomPasswordResetView(PasswordResetView):
    form_class = PasswordResetRequestForm
    template_name = 'armpad/password_reset.html'
    email_template_name = 'armpad/emails/password_reset_email.txt'
    html_email_template_name = 'armpad/emails/password_reset_email.html'
    subject_template_name = 'armpad/emails/password_reset_subject.txt'
    success_url = reverse_lazy('users_web:password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            return super().form_valid(form)
        else:
            return redirect(self.success_url)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = StyledSetPasswordForm
    template_name = 'armpad/password_reset_confirm.html'
    success_url = reverse_lazy('users_web:password_reset_complete')


# ═══════════════════════════════════════════════════════════
# VÉRIFICATION EMAIL
# ═══════════════════════════════════════════════════════════
def verify_email(request, token):
    """Vérifie un token de vérification d'email."""
    User = get_user_model()

    try:
        user = User.objects.get(email_verification_token=token)
    except User.DoesNotExist:
        messages.error(request, "Lien invalide ou déjà utilisé.")
        return redirect('users_web:login')

    # Vérifier l'expiration (7 jours)
    if user.email_verification_sent_at:
        expiration = user.email_verification_sent_at + timedelta(days=7)
        if timezone.now() > expiration:
            messages.error(request, "Ce lien a expiré. Demandez-en un nouveau.")
            return redirect('users_web:login')

    # Marquer comme vérifié
    user.email_verified = True
    user.email_verification_token = None
    user.save(update_fields=['email_verified', 'email_verification_token'])

    messages.success(request, "Votre email est vérifié ! Vous pouvez vous connecter.")
    return redirect('users_web:login')