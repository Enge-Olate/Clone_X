from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User
from .serializers import ProfileUpdateSerializer, UserRegistrationSerializer, UserPublicSerializer
# Create your views here.
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()
        login(self.request, user)
        
class SessionLoginAPIView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(
            request,
            username=username,
            password=password
        )
        if user is not None:
            login(request, user)
            return Response(
                UserPublicSerializer(user, context={"request": request}).data,
                status = status.HTTP_200_OK,
            )        
        return Response(
            {"detail": "Credenciais inválidas. Verifique seu @usuário e senha."},
            status = status.HTTP_401_UNAUTHORIZED,
        )

class SessionLogoutAPIView(views.APIView):
    """Endpoint REST para encerramento seguro de sessão."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({"detail": "Logout efetuado com sucesso."}, status=status.HTTP_200_OK)


        
class UserViewSet(viewsets.GenericViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    
    queryset = User.objects.all()
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "username"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get("q")
        if search_query:
            queryset = queryset.filter(username__icontains=search_query) | queryset.filter(
                display_name__icontains=search_query
            )
        return queryset.distinct()

    @action(detail=False, methods=["get", "patch", "put"], url_path="me")
    def me(self, request):
        if request.method == "GET":
            serializer = UserPublicSerializer(request.user, context={"request": request})
            return Response(serializer.data)

        serializer = ProfileUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserPublicSerializer(user, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post", "delete"], url_path="follow")
    def toggle_follow(self, request, username=None):
        target_user = self.get_object()
        if target_user == request.user:
            return Response(
                {"detail": "Você não pode seguir a si mesmo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "DELETE" or (
            request.method == "POST" and request.user.is_following(target_user)
            and request.query_params.get("toggle") == "true"
        ):
            request.user.unfollow(target_user)
            return Response(
                {
                    "following": False,
                    "followers_count": target_user.followers_count,
                    "my_following_count": request.user.following_count,
                },
                status=status.HTTP_200_OK,
            )

        request.user.follow(target_user)
        return Response(
            {
                "following": True,
                "followers_count": target_user.followers_count,
                "my_following_count": request.user.following_count,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="followers")
    def followers_list(self, request, username=None):
        target_user = self.get_object()
        followers = User.objects.filter(following_relations__following=target_user)
        serializer = UserPublicSerializer(followers, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="following")
    def following_list(self, request, username=None):
        target_user = self.get_object()
        following = User.objects.filter(followers_relations__follower=target_user)
        serializer = UserPublicSerializer(following, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)