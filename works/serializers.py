from rest_framework import serializers
from .models import Genre, Work, Chapter, Comment, Like, Library, ReadingProgress

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name_fr', 'name_en', 'slug']

class WorkListSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    genre_name = serializers.CharField(source='genre.name_fr', read_only=True, default='')

    class Meta:
        model = Work
        fields = ['id', 'title', 'summary', 'cover', 'author_username', 'genre_name',
                  'language', 'status', 'is_premium', 'likes_count', 'views_count',
                  'comments_count', 'published_at', 'created_at']
        read_only_fields = fields

class WorkDetailSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    genre = GenreSerializer(read_only=True)

    class Meta:
        model = Work
        fields = '__all__'
        read_only_fields = ['author', 'likes_count', 'views_count', 'comments_count', 'created_at', 'updated_at']

class ChapterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'work', 'title', 'order', 'is_draft', 'is_premium',
                  'likes_count', 'comments_count', 'views_count', 'created_at']
        read_only_fields = fields

class ChapterDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = '__all__'
        read_only_fields = ['work', 'likes_count', 'comments_count', 'views_count', 'created_at', 'updated_at']

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'work', 'chapter', 'parent', 'replies',
                  'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['author', 'likes_count', 'created_at', 'updated_at']

    def get_replies(self, obj):
        if obj.parent is None:
            return CommentSerializer(obj.replies.all(), many=True).data
        return None

class ReadingProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingProgress
        fields = ['id', 'user', 'work', 'last_chapter', 'progress_percent', 'updated_at']
        read_only_fields = ['user', 'work', 'updated_at']

class LibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ['id', 'user', 'work', 'added_at']
        read_only_fields = ['user', 'work', 'added_at']