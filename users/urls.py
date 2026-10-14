from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # ─── API Auth ───
    path('register/', views.RegisterView.as_view(), name='api_register'),
    path('me/', views.MeView.as_view(), name='api_me'),
    path('me/password/', views.ChangePasswordView.as_view(), name='api_change_password'),

    # ─── API Profil (slug) ───
    path('profile/<slug:slug>/', views.UserProfileView.as_view(), name='api_profile'),

    # ─── API Follow (slug) ───
    path('follow/<slug:slug>/', views.FollowToggleView.as_view(), name='api_follow_toggle'),

    # ─── API Préférences ───
    path('theme/', views.SetThemeView.as_view(), name='api_set_theme'),
    path('language/', views.SetLanguageView.as_view(), name='api_set_language'),

    # ─── API Notifications ───
    path('notifications/', views.NotificationListView.as_view(), name='api_notifications'),
    path('notifications/unread-count/', views.NotificationUnreadCountView.as_view(), name='api_notifications_unread'),
    path('notifications/read-all/', views.NotificationReadAllView.as_view(), name='api_notifications_read_all'),
    path('notifications/<int:pk>/read/', views.NotificationReadView.as_view(), name='api_notification_read'),

    # ─── API Chat (slug) ───
    path('chat/<slug:slug>/', views.ChatView.as_view(), name='api_chat'),
    path('react/<int:pk>/', views.ReactToMessageView.as_view(), name='api_react_message'),

    # ─── Follow (fonction, slug) ───
    path('follow/<slug:slug>/toggle/', views.toggle_follow, name='toggle_follow'),

    # ─── Followers / Following (slug) ───
    path('<slug:slug>/followers/', views.followers_list, name='followers_list'),
    path('<slug:slug>/following/', views.following_list, name='following_list'),
]
