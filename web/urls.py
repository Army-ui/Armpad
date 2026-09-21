from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from .forms import EmailAuthenticationForm
from users import views as users_views

app_name = 'web'

urlpatterns = [
    # Accueil et catalogue
    path('', views.HomeView.as_view(), name='home'),
    path('catalogue/', views.CatalogueView.as_view(), name='catalogue'),

    # Œuvres et chapitres
    path('oeuvre/<uuid:pk>/', views.WorkDetailView.as_view(), name='work_detail'),
    path('oeuvre/<uuid:work_id>/chapitre/<int:order>/', views.ChapterReaderView.as_view(), name='reader'),

    # Écriture
    path('ecrire/', views.WorkEditorView.as_view(), name='write'),
    path('ecrire/<uuid:pk>/', views.WorkEditView.as_view(), name='edit_work'),
    path('oeuvre/<uuid:work_id>/chapitre/ajouter/', views.ChapterEditorView.as_view(), name='add_chapter'),
    path('chapitre/<int:pk>/editer/', views.ChapterEditView.as_view(), name='edit_chapter'),

    # Suppression
    path('oeuvre/<uuid:pk>/supprimer/', views.DeleteWorkView.as_view(), name='delete_work'),
    path('chapitre/<int:pk>/supprimer/', views.DeleteChapterView.as_view(), name='delete_chapter'),

    # Profil (ORDRE IMPORTANT)
    path('profil/modifier/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profil/<str:username>/', views.ProfileView.as_view(), name='profile'),

    # Bibliothèque
    path('ma-bibliotheque/', views.LibraryView.as_view(), name='library'),

    # Premium
    path('premium/', views.PremiumView.as_view(), name='premium'),

    # Chat
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('chat/<str:username>/', views.ChatConversationView.as_view(), name='chat_conversation'),

    # Pages légales
    path('conditions/', views.ConditionsView.as_view(), name='conditions'),
    path('confidentialite/', views.ConfidentialiteView.as_view(), name='confidentialite'),

    path('register/', views.RegisterView.as_view(), name='register'),
    
    # API interne (AJAX)
    path('api/set-theme/', views.set_theme, name='set_theme'),
    path('api/library/<uuid:work_id>/toggle/', views.ToggleLibraryView.as_view(), name='toggle_library'),
    path('api/like/<uuid:work_id>/toggle/', views.ToggleLikeView.as_view(), name='toggle_like'),
    path('api/chapter/<int:pk>/like/', views.ToggleChapterLikeView.as_view(), name='toggle_chapter_like'),
    path('api/comment/<int:pk>/like/', views.ToggleCommentLikeView.as_view(), name='toggle_comment_like'),
    path('oeuvre/<uuid:pk>/commenter/', views.AddCommentView.as_view(), name='add_comment'),
    path('api/reading-progress/', views.UpdateReadingProgressView.as_view(), name='update_progress'),

    # Notifications (pages HTML)
    path('notifications/', users_views.notifications_page, name='notifications'),
    path('notifications/<int:pk>/read/', users_views.mark_notification_read, name='notification_read'),
    path('notifications/read-all/', users_views.mark_all_read, name='notifications_read_all'),
    path('notifications/unread-count/', users_views.unread_count, name='notifications_unread_count'),
    
        # Abonnés / Abonnements
    path('profil/<str:username>/followers/', users_views.followers_list, name='followers_list'),
    path('profil/<str:username>/following/', users_views.following_list, name='following_list'),
]