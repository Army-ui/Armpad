from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Follow, Message, Notification


# ═══════════════════════════════════════════════════════════
# FORMULAIRES ADMIN
# ═══════════════════════════════════════════════════════════
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


# ═══════════════════════════════════════════════════════════
# ADMIN UTILISATEUR
# ═══════════════════════════════════════════════════════════
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = (
        'username',
        'email',
        'is_staff',
        'is_active',
        'preferred_language',
        'theme',
        'date_joined',
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'preferred_language', 'theme')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'bio', 'avatar')
        }),
        ('Préférences', {
            'fields': ('preferred_language', 'theme')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'email')
    ordering = ('-date_joined',)


# ═══════════════════════════════════════════════════════════
# ADMIN FOLLOW
# ═══════════════════════════════════════════════════════════
@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followed', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'followed__username')
    raw_id_fields = ('follower', 'followed')


# ═══════════════════════════════════════════════════════════
# ADMIN MESSAGE
# ═══════════════════════════════════════════════════════════
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'content')
    raw_id_fields = ('sender', 'receiver')

    def content_preview(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = "Contenu"


# ═══════════════════════════════════════════════════════════
# ADMIN NOTIFICATION
# ═══════════════════════════════════════════════════════════
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'sender', 'type', 'message_preview', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'sender__username', 'message')
    raw_id_fields = ('user', 'sender')

    def message_preview(self, obj):
        return obj.message[:60] + ('...' if len(obj.message) > 60 else '')
    message_preview.short_description = "Message"