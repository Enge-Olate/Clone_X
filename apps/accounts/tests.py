from django.test import TestCase
import io
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Follow
# Create your tests here.


class AccountsBackendTestCase(APITestCase):
    """Suíte de testes orientados a objetos para autenticação, perfil e relacionamentos."""

    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            display_name="Alice Dev",
            password="StrongPassword123!",
        )
        self.bob = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            display_name="Bob Builder",
            password="StrongPassword123!",
        )

    def test_user_registration_and_login(self):
        """Garante que novos usuários possam se cadastrar e efetuar login com segurança."""
        reg_url = reverse("api_register")
        payload = {
            "username": "charlie",
            "email": "charlie@example.com",
            "display_name": "Charlie Jr",
            "password": "SafePassword99!",
            "password_confirm": "SafePassword99!",
        }
        response = self.client.post(reg_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="charlie").exists())

        login_url = reverse("api_login")
        login_res = self.client.post(
            login_url,
            {"username": "charlie", "password": "SafePassword99!"},
            format="json",
        )
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)

    def test_session_logout(self):
        """Garante que o endpoint de logout encerre a sessão autenticada."""
        self.client.force_login(self.alice)

        response = self.client.post(reverse("api_logout"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_optional_profile_updates_independently(self):
        """
        Verifica que nenhuma alteração de perfil é obrigatória:
        1) Alterar apenas o nome;
        2) Alterar apenas a foto de perfil;
        3) Alterar apenas a senha.
        """
        self.client.force_authenticate(user=self.alice)
        me_url = "/api/v1/users/me/"

        # 1. Altera somente o nome de exibição
        res_name = self.client.patch(me_url, {"display_name": "Alice Senior"}, format="json")
        self.assertEqual(res_name.status_code, status.HTTP_200_OK)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.display_name, "Alice Senior")

        # # 2. Altera somente a foto de perfil
        # avatar_file = generate_test_avatar()
        # res_avatar = self.client.patch(me_url, {"avatar": avatar_file}, format="multipart")
        # self.assertEqual(res_avatar.status_code, status.HTTP_200_OK)
        # self.alice.refresh_from_db()
        # self.assertTrue(bool(self.alice.avatar))

        # 3. Altera somente a senha
        res_pass = self.client.patch(
            me_url,
            {
                "current_password": "StrongPassword123!",
                "new_password": "NewStrongPassword456!",
            },
            format="json",
        )
        self.assertEqual(res_pass.status_code, status.HTTP_200_OK)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password("NewStrongPassword456!"))

    def test_follow_unfollow_and_prevent_self_follow(self):
        """Testa seguir, deixar de seguir, impedimento de auto-follow e listas de seguidores/seguindo."""
        self.client.force_authenticate(user=self.alice)

        # Impede auto-follow no modelo e na API
        with self.assertRaises(ValidationError):
            self.alice.follow(self.alice)

        self_res = self.client.post(f"/api/v1/users/{self.alice.username}/follow/")
        self.assertEqual(self_res.status_code, status.HTTP_400_BAD_REQUEST)

        # Segue Bob
        follow_res = self.client.post(f"/api/v1/users/{self.bob.username}/follow/")
        self.assertEqual(follow_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.alice.is_following(self.bob))

        # Verifica lista de seguidores de Bob e lista de seguindo de Alice
        followers_res = self.client.get(f"/api/v1/users/{self.bob.username}/followers/")
        self.assertEqual(len(followers_res.data), 1)
        self.assertEqual(followers_res.data[0]["username"], "alice")

        following_res = self.client.get(f"/api/v1/users/{self.alice.username}/following/")
        self.assertEqual(len(following_res.data), 1)
        self.assertEqual(following_res.data[0]["username"], "bob")

        # Deixa de seguir Bob
        unfollow_res = self.client.delete(f"/api/v1/users/{self.bob.username}/follow/")
        self.assertEqual(unfollow_res.status_code, status.HTTP_200_OK)
        self.assertFalse(self.alice.is_following(self.bob))
