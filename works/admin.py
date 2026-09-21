from django.contrib import admin
from .models import (
    Genre, Work, Chapter, ChapterImage,
    Comment, Like, Library, ReadingProgress, WorkView
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name_fr', 'name_en', 'slug')
    prepopulated_fields = {'slug': ('name_en',)}


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'genre', 'is_premium', 'published_at')
    list_filter = ('status', 'is_premium', 'language', 'genre')
    search_fields = ('title', 'author__username', 'tags')
    raw_id_fields = ('author',)


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'work', 'order', 'is_draft', 'is_premium')
    list_filter = ('is_draft', 'is_premium')
    raw_id_fields = ('work',)


@admin.register(ChapterImage)
class ChapterImageAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'order', 'caption')
    raw_id_fields = ('chapter',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'work', 'chapter', 'content', 'created_at')
    raw_id_fields = ('user', 'work', 'chapter', 'parent')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'work', 'chapter', 'comment', 'created_at')
    raw_id_fields = ('user', 'work', 'chapter', 'comment')


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('user', 'work', 'added_at')
    raw_id_fields = ('user', 'work')


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'work', 'chapter', 'last_read_at')
    raw_id_fields = ('user', 'work', 'chapter')


@admin.register(WorkView)
class WorkViewAdmin(admin.ModelAdmin):
    list_display = ('work', 'user', 'ip_address', 'viewed_at')
    raw_id_fields = ('work', 'user')