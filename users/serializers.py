from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import Follow

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ('username', 'email', 'password', 'password_confirm', 'preferred_language', 'theme')

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(_("Ce nom d'utilisateur est déjà pris."))
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("Cette adresse email est déjà utilisée."))
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(_("Les mots de passe ne correspondent pas."))
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model        = User
        fields       = ('id', 'username', 'bio', 'avatar', 'is_premium', 'followers_count', 'following_count', 'date_joined')
        read_only_fields = fields


class UserPrivateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ('id', 'username', 'email', 'bio', 'avatar', 'preferred_language',
                  'theme', 'is_premium', 'followers_count', 'following_count', 'date_joined')
        read_only_fields = ('id', 'email', 'is_premium', 'followers_count', 'following_count', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    old_password         = serializers.CharField(write_only=True)
    new_password         = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(_("Les nouveaux mots de passe ne correspondent pas."))
        return data