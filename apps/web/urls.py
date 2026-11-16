from django.urls import path
from .views import AuthPageView, HomeFeedview, UserProfileViw
""" Rotas WEB"""
urlpatterns = [
    path("", HomeFeedview.as_view(), name="web_feed"),
    path("login/", AuthPageView.as_view(), name="web_login"),
    path("u/<str:username>/", UserProfileViw.as_view(), name="web_profile")
]