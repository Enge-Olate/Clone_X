from django.urls import path
from .views import RegisterAPIView, SessionLoginAPIView, SessionLogoutAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="api_register"),
    path("login/", SessionLoginAPIView.as_view(), name="api_login"),
    path("logout/", SessionLogoutAPIView.as_view(), name="api_logout"),
]