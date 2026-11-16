from django.shortcuts import get_list_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, TemplateView
from apps.accounts.models import User
from apps.posts.models import Post

# Create your views here.
class AuthPageView(TemplateView):
    template_name = "auth/login_register.html"
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("web_feed")
        return super().dispatch(request, *args, **kwargs)

class HomeFeedview(LoginRequiredMixin, TemplateView):
    template_name = "feed/index.html"
    login_url = "/login/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["feed_posts"] = Post.objects.following_feed_for(user)[:50]
        context["suggested_users"] = (
            User.objects.exclude(id=user.id)
            .exclude(followers_relations_follower=user)[:5]
        )
        return context

class UserProfileViw(LoginRequiredMixin, DetailView):
    model=User
    template_name = "profile/detail.html"
    context_object_name= "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"
    login_url = "/login/"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        viewer = self.request.user
        context["user_posts"]=(
            Post.objects.filter(author=profile_user).interaction_metrics(viewer).order_by("-created_at")
        )
        context["followers_list"] = User.objects.filter(
            following_relations_following= profile_user
        )
        context["following_list"] = User.objects.filter(
                    followers_relations_follower= profile_user
        )
        context["is_following_profile"] = viewer.is_following(profile_user)
        context["suggested_user"] =(
            User.objects.exclude(
                id=viewer.id
            ).exclude(followers_relations_follower=viewer)[:5]
        )
        return context