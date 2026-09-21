from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.db.models import Q
import json

from works.models import (
    Work, Chapter, ChapterImage, Genre,
    Library, Like, Comment, ReadingProgress
)
from works.forms import WorkForm, ChapterForm, ChapterImageFormSet
from users.models import User, Notification
from subscriptions.models import Plan
from .forms import ProfileEditForm, UserRegistrationForm


# ═══════════════════════════════════════════════════════════
# PAGES PUBLIQUES
# ═══════════════════════════════════════════════════════════

class HomeView(TemplateView):
    template_name = 'armpad/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_works'] = Work.objects.filter(
            status__in=['ongoing', 'completed']
        ).order_by('-published_at')[:10]
        context['trending_works'] = Work.objects.filter(
            status__in=['ongoing', 'completed']
        ).order_by('-likes_count')[:4]
        context['genres'] = Genre.objects.all().order_by('name_fr')
        return context


class CatalogueView(ListView):
    model = Work
    template_name = 'armpad/catalogue.html'
    context_object_name = 'works'
    paginate_by = 20

    def get_queryset(self):
        qs = Work.objects.filter(
            status__in=['ongoing', 'completed']
        ).select_related('author', 'genre').order_by('-published_at')

        genre = self.request.GET.get('genre')
        if genre:
            qs = qs.filter(genre__slug=genre)

        # ═══ Recherche multi-critères : titre, auteur, tags ═══
        search = self.request.GET.get('search')
        if search:
            search = search.strip()
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(author__username__icontains=search) |
                Q(tags__icontains=search) |
                Q(summary__icontains=search)
            ).distinct()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all().order_by('name_fr')
        return context


class WorkDetailView(DetailView):
    model = Work
    template_name = 'armpad/work_detail.html'
    context_object_name = 'work'

    def get(self, request, *args, **kwargs):
        work = self.get_object()
        if request.user.is_authenticated and request.GET.get('continue') == '1':
            progress = ReadingProgress.objects.filter(
                user=request.user, work=work
            ).first()
            if progress and progress.chapter:
                return redirect('web:reader', work_id=work.id, order=progress.chapter.order)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        work = self.get_object()
        user = self.request.user

        chapters = work.chapters.filter(is_draft=False).order_by('order')
        if user.is_authenticated and work.author == user:
            chapters = work.chapters.all().order_by('order')
        context['chapters'] = chapters

        context['is_in_library'] = (
            user.is_authenticated and
            user.library.filter(work=work).exists()
        )

        context['user_liked'] = (
            user.is_authenticated and
            user.likes.filter(work=work, chapter=None, comment=None).exists()
        )

        context['comments'] = work.comments.filter(parent=None).order_by('-is_pinned', '-created_at')

        if user.is_authenticated:
            progress = ReadingProgress.objects.filter(user=user, work=work).first()
            context['progress'] = progress
            context['last_chapter'] = progress.chapter if progress else None
        else:
            context['progress'] = None
            context['last_chapter'] = None

        return context


class ChapterReaderView(DetailView):
    model = Chapter
    template_name = 'armpad/reader.html'
    context_object_name = 'chapter'
    slug_field = 'order'
    slug_url_kwarg = 'order'

    def get_queryset(self):
        work_id = self.kwargs['work_id']
        work = get_object_or_404(Work, id=work_id)
        user = self.request.user
        qs = Chapter.objects.filter(work=work).order_by('order')
        if user.is_authenticated and work.author == user:
            return qs
        return qs.filter(is_draft=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chapter = self.get_object()
        work = chapter.work
        context['work'] = work

        chapters = work.chapters.filter(is_draft=False).order_by('order')
        if self.request.user.is_authenticated and work.author == self.request.user:
            chapters = work.chapters.all().order_by('order')
        context['prev_chapter'] = chapters.filter(order__lt=chapter.order).last()
        context['next_chapter'] = chapters.filter(order__gt=chapter.order).first()

        context['user_liked_chapter'] = (
            self.request.user.is_authenticated and
            self.request.user.likes.filter(chapter=chapter).exists()
        )

        context['chapter_comments'] = chapter.comments.filter(parent=None).order_by('-created_at')

        # ═══ CRUCIAL : Vérifier si l'œuvre est dans la bibliothèque ═══
        context['is_in_library'] = (
            self.request.user.is_authenticated and
            self.request.user.library.filter(work=work).exists()
        )

        # ═══ POSITION DE SCROLL SAUVEGARDÉE ═══
        saved_scroll = 0
        if self.request.user.is_authenticated:
            progress = ReadingProgress.objects.filter(
                user=self.request.user, work=work
            ).first()
            if progress and progress.chapter_id == chapter.id:
                saved_scroll = progress.scroll_position
        context['saved_scroll'] = saved_scroll

        return context


# ═══════════════════════════════════════════════════════════
# CRÉATION / ÉDITION D'ŒUVRE
# ═══════════════════════════════════════════════════════════

class WorkEditorView(LoginRequiredMixin, CreateView):
    model = Work
    form_class = WorkForm
    template_name = 'armpad/work_editor.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        self.object = form.save()
        messages.success(self.request, "Œuvre créée ! Ajoutez maintenant des chapitres.")
        return redirect('web:edit_work', pk=self.object.pk)


class WorkEditView(LoginRequiredMixin, UpdateView):
    model = Work
    form_class = WorkForm
    template_name = 'armpad/work_editor.html'

    def get_queryset(self):
        return Work.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapters'] = self.object.chapters.all().order_by('order')
        context['is_editing'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, "Œuvre mise à jour.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('web:edit_work', kwargs={'pk': self.object.pk})


# ═══════════════════════════════════════════════════════════
# CHAPITRES
# ═══════════════════════════════════════════════════════════

class ChapterEditorView(LoginRequiredMixin, CreateView):
    model = Chapter
    form_class = ChapterForm
    template_name = 'armpad/chapter_editor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        work = get_object_or_404(Work, id=self.kwargs['work_id'], author=self.request.user)
        context['work'] = work
        context['is_editing'] = False
        if self.request.POST:
            context['image_formset'] = ChapterImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['image_formset'] = ChapterImageFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        work = get_object_or_404(Work, id=self.kwargs['work_id'], author=self.request.user)
        form.instance.work = work
        last_order = work.chapters.aggregate(models.Max('order'))['order__max'] or 0
        form.instance.order = last_order + 1
        self.object = form.save()
        if image_formset.is_valid():
            image_formset.instance = self.object
            image_formset.save()
        messages.success(self.request, f"Chapitre {self.object.order} ajouté !")
        return redirect('web:edit_work', pk=work.pk)


class ChapterEditView(LoginRequiredMixin, UpdateView):
    model = Chapter
    form_class = ChapterForm
    template_name = 'armpad/chapter_editor.html'

    def get_queryset(self):
        return Chapter.objects.filter(work__author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['work'] = self.object.work
        context['is_editing'] = True
        if self.request.POST:
            context['image_formset'] = ChapterImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['image_formset'] = ChapterImageFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        self.object = form.save()
        if image_formset.is_valid():
            image_formset.instance = self.object
            image_formset.save()
        messages.success(self.request, "Chapitre mis à jour.")
        return redirect('web:edit_work', pk=self.object.work.pk)


# ═══════════════════════════════════════════════════════════
# SUPPRESSION
# ═══════════════════════════════════════════════════════════

class DeleteWorkView(LoginRequiredMixin, View):
    def post(self, request, pk):
        work = get_object_or_404(Work, pk=pk, author=request.user)
        title = work.title
        work.delete()
        messages.success(request, f"L'œuvre « {title} » a été supprimée.")
        return redirect('web:home')


class DeleteChapterView(LoginRequiredMixin, View):
    def post(self, request, pk):
        chapter = get_object_or_404(Chapter, pk=pk, work__author=request.user)
        work_pk = chapter.work.pk
        order = chapter.order
        chapter.delete()
        messages.success(request, f"Le chapitre {order} a été supprimé.")
        return redirect('web:edit_work', pk=work_pk)


# ═══════════════════════════════════════════════════════════
# PROFIL
# ═══════════════════════════════════════════════════════════

class ProfileView(DetailView):
    model = User
    template_name = 'armpad/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile_user = self.get_object()

        is_following = (
            user.is_authenticated and
            user.following.filter(followed=profile_user).exists()
        )
        is_follower = (
            user.is_authenticated and
            user.followers.filter(follower=profile_user).exists()
        )

        context['is_following'] = is_following
        context['is_follower'] = is_follower
        context['is_friend'] = is_following and is_follower

        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'armpad/profile_edit.html'
    form_class = ProfileEditForm

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('web:profile', kwargs={'username': self.request.user.username})

    def form_valid(self, form):
        messages.success(self.request, "Votre profil a été mis à jour.")
        return super().form_valid(form)


# ═══════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════

class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'armpad/register.html'
    success_url = reverse_lazy('web:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object, backend='users.backends.EmailBackend')
        messages.success(self.request, "Bienvenue sur Armpad !")
        return response


# ═══════════════════════════════════════════════════════════
# BIBLIOTHÈQUE
# ═══════════════════════════════════════════════════════════

class LibraryView(LoginRequiredMixin, ListView):
    template_name = 'armpad/library.html'
    context_object_name = 'library_items'

    def get_queryset(self):
        items = list(
            self.request.user.library.all()
            .select_related('work', 'work__author')
            .order_by('-added_at')
        )
        for item in items:
            progress = ReadingProgress.objects.filter(
                user=self.request.user, work=item.work
            ).first()
            item.progress_percent = progress.progress_percent if progress else 0
            item.resume_order = progress.chapter.order if (progress and progress.chapter) else 1
            if progress and progress.last_read_at:
                item.has_update = item.work.last_update_at and item.work.last_update_at > progress.last_read_at
            else:
                item.has_update = False
        return items


# ═══════════════════════════════════════════════════════════
# API : TOGGLE LIBRARY
# ═══════════════════════════════════════════════════════════

class ToggleLibraryView(View):   # ← retirez LoginRequiredMixin
    def post(self, request, work_id):
        # Si non connecté, on renvoie un JSON avec un flag
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'not_authenticated',
                'redirect_url': '/login/?next=' + request.META.get('HTTP_REFERER', '/'),
            }, status=200)

        work = get_object_or_404(Work, pk=work_id)
        item = Library.objects.filter(user=request.user, work=work).first()
        if item:
            item.delete()
            is_in = False
        else:
            Library.objects.create(user=request.user, work=work)
            is_in = True
        return JsonResponse({'is_in_library': is_in, 'status': 'ok'})
    
# ═══════════════════════════════════════════════════════════
# API : TOGGLE LIKE ŒUVRE
# ═══════════════════════════════════════════════════════════

class ToggleLikeView(LoginRequiredMixin, View):
    def post(self, request, work_id):
        work = get_object_or_404(Work, pk=work_id)
        like = Like.objects.filter(user=request.user, work=work).first()
        if like:
            like.delete()
            work.likes_count = max(0, work.likes_count - 1)
            work.save(update_fields=['likes_count'])
            user_liked = False
        else:
            Like.objects.create(user=request.user, work=work)
            work.likes_count += 1
            work.save(update_fields=['likes_count'])
            user_liked = True
        return JsonResponse({'status': 'ok', 'user_liked': user_liked, 'likes_count': work.likes_count})


# ═══════════════════════════════════════════════════════════
# API : TOGGLE LIKE CHAPITRE
# ═══════════════════════════════════════════════════════════

class ToggleChapterLikeView(LoginRequiredMixin, View):
    def post(self, request, pk):
        chapter = get_object_or_404(Chapter, pk=pk)
        like = Like.objects.filter(user=request.user, chapter=chapter).first()
        if like:
            like.delete()
            chapter.likes_count = max(0, chapter.likes_count - 1)
            chapter.save(update_fields=['likes_count'])
            user_liked = False
        else:
            Like.objects.create(user=request.user, chapter=chapter)
            chapter.likes_count += 1
            chapter.save(update_fields=['likes_count'])
            user_liked = True
        return JsonResponse({'status': 'ok', 'user_liked': user_liked, 'likes_count': chapter.likes_count})


# ═══════════════════════════════════════════════════════════
# API : TOGGLE LIKE COMMENTAIRE
# ═══════════════════════════════════════════════════════════

class ToggleCommentLikeView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        like = Like.objects.filter(user=request.user, comment=comment).first()
        if like:
            like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
            user_liked = False
        else:
            Like.objects.create(user=request.user, comment=comment)
            comment.likes_count += 1
            user_liked = True
        comment.save(update_fields=['likes_count'])
        return JsonResponse({'status': 'ok', 'user_liked': user_liked, 'likes_count': comment.likes_count})


# ═══════════════════════════════════════════════════════════
# AJOUTER UN COMMENTAIRE
# ═══════════════════════════════════════════════════════════

class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        work = get_object_or_404(Work, pk=pk)
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        chapter_id = request.POST.get('chapter_id')
        next_url = request.POST.get('next', '')

        if not content:
            messages.error(request, "Le commentaire ne peut pas être vide.")
            if next_url:
                return redirect(next_url)
            return redirect('web:work_detail', pk=work.pk)

        parent = None
        if parent_id:
            parent = Comment.objects.filter(pk=parent_id).first()

        chapter = None
        if chapter_id:
            chapter = Chapter.objects.filter(pk=chapter_id, work=work).first()

        Comment.objects.create(
            user=request.user,
            work=work,
            chapter=chapter,
            parent=parent,
            content=content
        )

        messages.success(request, "Commentaire publié !")

        if next_url:
            return redirect(next_url)
        return redirect('web:work_detail', pk=work.pk)


# ═══════════════════════════════════════════════════════════
# API : PROGRESSION DE LECTURE
# ═══════════════════════════════════════════════════════════

class UpdateReadingProgressView(LoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)
        work_id = data.get('work_id')
        chapter_id = data.get('chapter_id')
        percent = int(data.get('percent', 0))
        scroll_position = int(data.get('scroll_position', 0))

        work = get_object_or_404(Work, pk=work_id)
        chapter = Chapter.objects.filter(pk=chapter_id).first()

        ReadingProgress.objects.update_or_create(
            user=request.user,
            work=work,
            defaults={
                'chapter': chapter,
                'progress_percent': min(100, max(0, percent)),
                'scroll_position': max(0, scroll_position),
            }
        )
        return JsonResponse({'status': 'ok'})


# ═══════════════════════════════════════════════════════════
# CHAT — Conversation avec un utilisateur
# ═══════════════════════════════════════════════════════════

class ChatConversationView(LoginRequiredMixin, View):
    def get(self, request, username):
        from users.models import Message, Follow
        other = get_object_or_404(User, username=username)

        are_friends = (
            Follow.objects.filter(follower=request.user, followed=other).exists() and
            Follow.objects.filter(follower=other, followed=request.user).exists()
        )

        messages_qs = Message.objects.filter(
            models.Q(sender=request.user, receiver=other) |
            models.Q(sender=other, receiver=request.user)
        ).order_by('created_at')

        messages_qs.filter(sender=other, receiver=request.user, is_read=False).update(is_read=True)

        return render(request, 'armpad/chat_conversation.html', {
            'other': other,
            'chat_messages': messages_qs,
            'are_friends': are_friends,
        })


# ═══════════════════════════════════════════════════════════
# PREMIUM
# ═══════════════════════════════════════════════════════════

class PremiumView(TemplateView):
    template_name = 'armpad/premium.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = Plan.objects.filter(is_active=True).order_by('price')

        if self.request.user.is_authenticated:
            from django.utils import timezone
            try:
                from subscriptions.models import Subscription
                active_sub = Subscription.objects.filter(
                    user=self.request.user,
                    is_active=True,
                    end_date__gt=timezone.now()
                ).first()
                context['active_subscription'] = active_sub
            except Exception:
                context['active_subscription'] = None
        return context


# ═══════════════════════════════════════════════════════════
# CHAT — Page principale
# ═══════════════════════════════════════════════════════════

class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'armpad/chat.html'

    def get_context_data(self, **kwargs):
        from users.models import Follow, Message
        from django.db.models import Q

        context = super().get_context_data(**kwargs)
        user = self.request.user

        conversations_ids = set()
        sent = Message.objects.filter(sender=user).values_list('receiver', flat=True)
        received = Message.objects.filter(receiver=user).values_list('sender', flat=True)
        conversations_ids.update(sent)
        conversations_ids.update(received)

        conversations = []
        for other_id in conversations_ids:
            other = User.objects.filter(id=other_id).first()
            if not other:
                continue

            last_msg = Message.objects.filter(
                Q(sender=user, receiver=other) | Q(sender=other, receiver=user)
            ).order_by('-created_at').first()

            unread_count = Message.objects.filter(
                sender=other, receiver=user, is_read=False
            ).count()

            conversations.append({
                'user': other,
                'last_message': last_msg,
                'unread_count': unread_count,
            })

        conversations.sort(
            key=lambda c: c['last_message'].created_at if c['last_message'] else 0,
            reverse=True
        )

        context['conversations'] = conversations
        return context


# ═══════════════════════════════════════════════════════════
# PAGES LÉGALES
# ═══════════════════════════════════════════════════════════

class ConditionsView(TemplateView):
    template_name = 'armpad/conditions.html'


class ConfidentialiteView(TemplateView):
    template_name = 'armpad/confidentialite.html'


# ═══════════════════════════════════════════════════════════
# API : THÈME
# ═══════════════════════════════════════════════════════════

@csrf_exempt
def set_theme(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        theme = data.get('theme')
        if theme not in ('light', 'dark'):
            return JsonResponse({'error': 'Thème invalide'}, status=400)
        if request.user.is_authenticated:
            request.user.theme = theme
            request.user.save(update_fields=['theme'])
        else:
            request.session['theme'] = theme
        return JsonResponse({'status': 'ok', 'theme': theme})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)