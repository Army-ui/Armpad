from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='api_register'),
    path('me/', views.MeView.as_view(), name='api_me'),
    path('me/password/', views.ChangePasswordView.as_view(), name='api_change_password'),
    path('profile/<str:username>/', views.UserProfileView.as_view(), name='api_profile'),
    path('follow/<str:username>/', views.FollowToggleView.as_view(), name='api_follow_toggle'),
    path('theme/', views.SetThemeView.as_view(), name='api_set_theme'),
    path('language/', views.SetLanguageView.as_view(), name='api_set_language'),

    path('notifications/', views.NotificationListView.as_view(), name='api_notifications'),
    path('notifications/unread-count/', views.NotificationUnreadCountView.as_view(), name='api_notifications_unread'),
    path('notifications/read-all/', views.NotificationReadAllView.as_view(), name='api_notifications_read_all'),
    path('notifications/<int:pk>/read/', views.NotificationReadView.as_view(), name='api_notification_read'),

    path('chat/<str:username>/', views.ChatView.as_view(), name='api_chat'),
    path('react/<int:pk>/', views.ReactToMessageView.as_view(), name='api_react_message'),

    path('follow/<str:username>/toggle/', views.toggle_follow, name='toggle_follow'),

    path('<str:username>/followers/', views.followers_list, name='followers_list'),
    path('<str:username>/following/', views.following_list, name='following_list'),
]