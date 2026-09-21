from rest_framework import generics, status, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import models as django_models
from django_filters.rest_framework import DjangoFilterBackend
from .models import Genre, Work, Chapter, Comment, Like, ReadingProgress, Library, WorkView
from .serializers import (
    GenreSerializer, WorkListSerializer, WorkDetailSerializer,
    ChapterListSerializer, ChapterDetailSerializer,
    CommentSerializer, ReadingProgressSerializer
)
from core.permissions import IsAuthorOrReadOnly, IsPremiumOrFreeContent


class GenreListView(generics.ListAPIView):
    queryset           = Genre.objects.all()
    serializer_class   = GenreSerializer
    permission_classes = [permissions.AllowAny]


class WorkListCreateView(generics.ListCreateAPIView):
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['genre', 'language', 'status', 'is_premium', 'author__username']
    search_fields    = ['title', 'summary', 'tags', 'author__username']
    ordering_fields  = ['created_at', 'views_count', 'likes_count']
    ordering         = ['-created_at']

    def get_queryset(self):
        qs = Work.objects.select_related('author', 'genre')
        if self.request.user.is_authenticated:
            return (qs.exclude(status='draft') |
                    qs.filter(status='draft', author=self.request.user)).distinct()
        return qs.exclude(status='draft')

    def get_serializer_class(self):
        return WorkDetailSerializer if self.request.method == 'POST' else WorkListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class WorkDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Work.objects.select_related('author', 'genre').prefetch_related('chapters')
    serializer_class   = WorkDetailSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_authenticated:
            _, created = WorkView.objects.get_or_create(work=instance, user=request.user)
        else:
            ip = request.META.get('REMOTE_ADDR')
            _, created = WorkView.objects.get_or_create(work=instance, user=None, ip_address=ip)
        if created:
            Work.objects.filter(pk=instance.pk).update(views_count=django_models.F('views_count') + 1)
            instance.refresh_from_db()
        return super().retrieve(request, *args, **kwargs)


class MyWorksView(generics.ListAPIView):
    serializer_class   = WorkListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Work.objects.filter(author=self.request.user).order_by('-updated_at')


class ChapterListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthorOrReadOnly]

    def get_work(self):
        return get_object_or_404(Work, pk=self.kwargs['work_id'])

    def get_queryset(self):
        return Chapter.objects.filter(work=self.get_work()).order_by('order')

    def get_serializer_class(self):
        return ChapterDetailSerializer if self.request.method == 'POST' else ChapterListSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        work = self.get_work()
        if work.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(_("Vous n'êtes pas l'auteur de cette œuvre."))
        serializer.save(work=work)
        # Notifier les abonnés de la bibliothèque
        try:
            from users.models import Notification
            for lib in Library.objects.filter(work=work).select_related('user'):
                if lib.user != self.request.user:
                    Notification.objects.create(
                        user=lib.user, sender=self.request.user, type='chapter',
                        message=f"Nouveau chapitre dans \"{work.title}\"",
                        link=f"/oeuvre/{work.id}/"
                    )
        except Exception:
            pass


class ChapterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChapterDetailSerializer
    lookup_field     = 'order'

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsAuthorOrReadOnly()]

    def get_queryset(self):
        return Chapter.objects.filter(work_id=self.kwargs['work_id'])

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Vérification premium
        if instance.is_premium or instance.work.is_premium:
            if not request.user.is_authenticated:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(_("Connectez-vous pour accéder au contenu Premium."))
            if instance.work.author != request.user and not request.user.is_staff:
                if not request.user.is_premium:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied(_("Abonnez-vous Premium pour lire ce chapitre."))
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        return super().retrieve(request, *args, **kwargs)


class LikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, work_id):
        work = get_object_or_404(Work, pk=work_id)
        if work.author == request.user:
            return Response({"error": "Vous ne pouvez pas liker votre propre œuvre."}, status=400)
        like, created = Like.objects.get_or_create(user=request.user, work=work, chapter=None, comment=None)
        if not created:
            like.delete()
            real = Like.objects.filter(work=work, chapter=None, comment=None).count()
            Work.objects.filter(pk=work_id).update(likes_count=real)
            return Response({"liked": False, "likes_count": real})
        real = Like.objects.filter(work=work, chapter=None, comment=None).count()
        Work.objects.filter(pk=work_id).update(likes_count=real)
        try:
            from users.models import Notification
            Notification.objects.create(
                user=work.author, sender=request.user, type='like',
                message=f"{request.user.username} a aimé votre œuvre \"{work.title}\"",
                link=f"/oeuvre/{work.id}/"
            )
        except Exception:
            pass
        return Response({"liked": True, "likes_count": real}, status=201)


class ChapterLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, work_id, order):
        chapter = get_object_or_404(Chapter, work_id=work_id, order=order)
        if chapter.work.author == request.user:
            return Response({"error": "Vous ne pouvez pas liker votre propre chapitre."}, status=400)
        like, created = Like.objects.get_or_create(user=request.user, chapter=chapter, work=None, comment=None)
        if not created:
            like.delete()
            real = Like.objects.filter(chapter=chapter).count()
            Chapter.objects.filter(pk=chapter.pk).update(likes_count=real)
            return Response({"liked": False, "likes_count": real})
        real = Like.objects.filter(chapter=chapter).count()
        Chapter.objects.filter(pk=chapter.pk).update(likes_count=real)
        return Response({"liked": True, "likes_count": real}, status=201)


class CommentLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, comment=comment, work=None, chapter=None)
        if not created:
            like.delete()
            real = Like.objects.filter(comment=comment).count()
            Comment.objects.filter(pk=pk).update(likes_count=real)
            return Response({"liked": False, "likes_count": real})
        real = Like.objects.filter(comment=comment).count()
        Comment.objects.filter(pk=pk).update(likes_count=real)
        try:
            from users.models import Notification
            if comment.author != request.user:
                Notification.objects.create(
                    user=comment.author, sender=request.user, type='like',
                    message=f"{request.user.username} a aimé votre commentaire",
                    link=f"/oeuvre/{comment.work_id}/" if comment.work_id else ""
                )
        except Exception:
            pass
        return Response({"liked": True, "likes_count": real}, status=201)


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class   = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(
            work_id=self.kwargs['work_id'], parent=None
        ).select_related('author').prefetch_related('replies__author').order_by('-likes_count', '-created_at')

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user, work_id=self.kwargs['work_id'])
        try:
            from users.models import Notification
            work = comment.work
            if work and work.author != self.request.user:
                Notification.objects.create(
                    user=work.author, sender=self.request.user, type='comment',
                    message=f"{self.request.user.username} a commenté votre œuvre \"{work.title}\"",
                    link=f"/oeuvre/{work.id}/"
                )
        except Exception:
            pass


class ChapterCommentListCreateView(generics.ListCreateAPIView):
    serializer_class   = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_chapter(self):
        return get_object_or_404(Chapter, work_id=self.kwargs['work_id'], order=self.kwargs['order'])

    def get_queryset(self):
        chapter = self.get_chapter()
        return Comment.objects.filter(
            chapter=chapter, parent=None
        ).select_related('author').prefetch_related('replies__author').order_by('-likes_count', '-created_at')

    def perform_create(self, serializer):
        chapter = self.get_chapter()
        comment = serializer.save(author=self.request.user, chapter=chapter)
        try:
            from users.models import Notification
            if chapter.work.author != self.request.user:
                Notification.objects.create(
                    user=chapter.work.author, sender=self.request.user, type='comment',
                    message=f"{self.request.user.username} a commenté votre chapitre \"{chapter.title}\"",
                    link=f"/oeuvre/{chapter.work_id}/chapitre/{chapter.order}/"
                )
        except Exception:
            pass


class LibraryToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, work_id):
        work = get_object_or_404(Work, pk=work_id)
        item, created = Library.objects.get_or_create(user=request.user, work=work)
        if not created:
            item.delete()
            return Response({'saved': False, 'message': 'Retiré de votre bibliothèque.'})
        return Response({'saved': True, 'message': 'Ajouté à votre bibliothèque !'}, status=201)

    def delete(self, request, work_id):
        Library.objects.filter(user=request.user, work_id=work_id).delete()
        return Response({'saved': False})


class ReadingProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, work_id):
        progress = get_object_or_404(ReadingProgress, user=request.user, work_id=work_id)
        return Response(ReadingProgressSerializer(progress).data)

    def post(self, request, work_id):
        work = get_object_or_404(Work, pk=work_id)
        progress, _ = ReadingProgress.objects.update_or_create(
            user=request.user, work=work,
            defaults={
                'last_chapter_id':  request.data.get('last_chapter'),
                'progress_percent': request.data.get('progress_percent', 0),
            }
        )
        return Response(ReadingProgressSerializer(progress).data)