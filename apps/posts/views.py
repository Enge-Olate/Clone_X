from django.shortcuts import render
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.permissions import IsAuthorOrReadOnly 
from .models import Post
from .serializers import PostSerializer, CommentSerializer
# Create your views here.

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    queryset =Post.objects.all()
    def get_quetyset(self):
        user = self.request.user
        author_username = self.request.query_params.get("author")
        if self.action in {
            "retrieve",
            "destroy",
            "update",
            "partial_update",
            "like",
            "comments",
        }:
            return Post.objects.interaction_metrics(user)

        if author_username:
            return(
                Post.objects.filter(author_username=author_username).interactions_metrics(user).order_by("-created_at")
            )
        return Post.objects.following_feed_for(user)

    def perform_create(self, serializer):
        serializer.save(author = self.request.user)
    
    @action(detail=False, methods = ["GET"], url_path="feed")
    def feed(self, request):
        queryset = Post.objects.following_feed_for(request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="like", permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        liked, total_likes = post.toggle_like(request.user)
        return Response(
            {"liked": liked, "likes_count": total_likes},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get", "post"], url_path="comments", permission_classes=[permissions.IsAuthenticated])
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == "GET":
            serializer = CommentSerializer(
                post.comments.select_related("author").all(),
                many=True,
                context={"request": request},
            )
            return Response(serializer.data)

        serializer = CommentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)