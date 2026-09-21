from django.urls import path
from . import views

app_name = 'works'

urlpatterns = [
    # Genres
    path('genres/', views.GenreListView.as_view(), name='genres'),

    # Œuvres
    path('works/', views.WorkListCreateView.as_view(), name='work-list'),
    path('works/my/', views.MyWorksView.as_view(), name='my-works'),
    path('works/<uuid:pk>/', views.WorkDetailView.as_view(), name='work-detail'),

    # Chapitres
    path('works/<uuid:work_id>/chapters/', views.ChapterListCreateView.as_view(), name='chapter-list'),
    path('works/<uuid:work_id>/chapters/<int:order>/', views.ChapterDetailView.as_view(), name='chapter-detail'),

    # Likes
    path('works/<uuid:work_id>/like/', views.LikeToggleView.as_view(), name='like-work'),
    path('works/<uuid:work_id>/chapters/<int:order>/like/', views.ChapterLikeToggleView.as_view(), name='like-chapter'),
    path('works/comments/<int:pk>/like/', views.CommentLikeToggleView.as_view(), name='like-comment'),

    # Commentaires
    path('works/<uuid:work_id>/comments/', views.CommentListCreateView.as_view(), name='work-comments'),
    path('works/<uuid:work_id>/chapters/<int:order>/comments/', views.ChapterCommentListCreateView.as_view(), name='chapter-comments'),

    # Bibliothèque
    path('works/<uuid:work_id>/library/', views.LibraryToggleView.as_view(), name='library-toggle'),

    # Progression
    path('works/<uuid:work_id>/progress/', views.ReadingProgressView.as_view(), name='progress'),
]