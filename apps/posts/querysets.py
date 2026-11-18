from django.db import models
from django.db.models import Count, Exists, OuterRef, Q

class PostQuerySet(models.QuerySet):
    def interactions_metrics(self, user=None):
        qs = self.select_related("author").prefetch_related("comments__author").annotate(
            likes_count = Count("likes", distinct=True),
            comments_count = Count("comments", distinct=True)
        )
        if user and user.is_authenticated:
            from .models import Like
            user_likes = Like.objects.filter(post = OuterRef("pk"), user=user)
            qs = qs.annotate(is_liked = Exists(user_likes))
        return qs
    
    def following_feed_for(self, user):
        if not user or not user.is_authenticated:
            return self.none()
        # return (
        #     self.filter(author__followers_relations__follower = user)
        #     .interactions_metrics(user).order_by("-created_at")
        # )
        return(
            self.filter(
                Q(author=user)|Q(author__followers_relations__follower = user)
            ).distinct().interactions_metrics(user).order_by("-created_at")
        )