from rest_framework import serializers
from apps.accounts.serializers import UserPublicSerializer
from .models import Comment, Post

class CommentSerializer(serializers.ModelSerilizer):
    author = UserPublicSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "content",
            "created_at"
        )
        read_only_posts = ("id", "post", "author", "created_at")

class PostSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True, default=0)
    comments_count = serializers.IntegerField(read_only=True, default=0)
    is_liked = serializers.BooleanField(read_only=True, default=False)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "content",
            "image",
            "likes_count",
            "comments_count",
            "is_liked",
            "comments",
            "created_at",
        ]
        read_only_fields=[
            "id",
            "author",
            "likes_count",
            "comments_count",
            "is_liked",
            "comments",
            "created_at"
        ]
    