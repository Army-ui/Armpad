import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify


# ═══════════════════════════════════════════════════════════
# GENRE
# ═══════════════════════════════════════════════════════════
class Genre(models.Model):
    name_en = models.CharField(max_length=100)
    name_fr = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
        ordering = ['name_fr']

    def __str__(self):
        return self.name_fr

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)

    @property
    def name(self):
        from django.utils.translation import get_language
        lang = get_language()
        if lang and lang.startswith('en'):
            return self.name_en
        return self.name_fr


# ═══════════════════════════════════════════════════════════
# WORK (ŒUVRE)
# ═══════════════════════════════════════════════════════════
class Work(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('ongoing', 'En cours'),
        ('completed', 'Terminé'),
        ('hiatus', 'En pause'),
    ]

    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
        ('de', 'Deutsch'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='works'
    )

    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    cover = models.ImageField(upload_to='works/covers/', null=True, blank=True)
    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='works'
    )
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='fr')
    tags = models.CharField(max_length=300, blank=True, help_text="Mots-clés séparés par des virgules")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    is_premium = models.BooleanField(default=False)

    likes_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_update_at = models.DateTimeField(auto_now=True, null=True, verbose_name="Dernière mise à jour")
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-published_at']
        verbose_name = "Œuvre"
        verbose_name_plural = "Œuvres"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('web:work_detail', kwargs={'pk': self.pk})

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def chapters_count(self):
        return self.chapters.filter(is_draft=False).count()


# ═══════════════════════════════════════════════════════════
# CHAPTER (CHAPITRE)
# ═══════════════════════════════════════════════════════════
class Chapter(models.Model):
    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name='chapters'
    )
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='chapters/covers/', null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    is_draft = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)

    likes_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ('work', 'order')
        verbose_name = "Chapitre"
        verbose_name_plural = "Chapitres"

    def __str__(self):
        return f"{self.work.title} - Ch. {self.order} : {self.title}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('web:reader', kwargs={'work_id': self.work.id, 'order': self.order})


# ═══════════════════════════════════════════════════════════
# CHAPTER IMAGE (style Webtoon)
# ═══════════════════════════════════════════════════════════
class ChapterImage(models.Model):
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='chapters/panels/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Image de chapitre"
        verbose_name_plural = "Images de chapitre"

    def __str__(self):
        return f"{self.chapter.title} - Image {self.order}"


# ═══════════════════════════════════════════════════════════
# COMMENT
# ═══════════════════════════════════════════════════════════
class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name='comments',
        null=True,
        blank=True
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='comments',
        null=True,
        blank=True
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True
    )
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    likes_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"

    def __str__(self):
        return f"{self.user.username} : {self.content[:40]}"


# ═══════════════════════════════════════════════════════════
# LIKE (sur œuvre, chapitre ou commentaire)
# ═══════════════════════════════════════════════════════════
class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name='likes',
        null=True,
        blank=True
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='likes',
        null=True,
        blank=True
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Like"
        verbose_name_plural = "Likes"

    def __str__(self):
        target = self.work or self.chapter or self.comment
        return f"{self.user.username} ♥ {target}"


# ═══════════════════════════════════════════════════════════
# LIBRARY (bibliothèque personnelle)
# ═══════════════════════════════════════════════════════════
class Library(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='library'
    )
    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name='in_libraries'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'work')
        ordering = ['-added_at']
        verbose_name = "Bibliothèque"
        verbose_name_plural = "Bibliothèques"

    def __str__(self):
        return f"{self.user.username} - {self.work.title}"


# ═══════════════════════════════════════════════════════════
# READING PROGRESS (progression de lecture)
# ═══════════════════════════════════════════════════════════
class ReadingProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_progress'
    )
    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name='reading_progress'
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='reading_progress',
        null=True,
        blank=True
    )
    progress_percent = models.PositiveIntegerField(default=0, verbose_name="Progression %")
    scroll_position = models.PositiveIntegerField(default=0, verbose_name="Position de scroll (px)")
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'work')
        verbose_name = "Progression de lecture"
        verbose_name_plural = "Progressions de lecture"

    def __str__(self):
        return f"{self.user.username} - {self.work.title} ({self.progress_percent}%)"


# ═══════════════════════════════════════════════════════════
# WORK VIEW (vues par œuvre)
# ═══════════════════════════════════════════════════════════
class WorkView(models.Model):
    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_views'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        verbose_name = "Vue d'œuvre"
        verbose_name_plural = "Vues d'œuvre"

    def __str__(self):
        return f"{self.work.title} - {self.viewed_at}"