from django.test import TestCase, Client
import pytest
from django.urls import reverse
from apps.accounts.models import User
from apps.posts.models import Post
# Create your tests here.
class FrontendTemplateTest(TestCase):
    def SetUp(self):
        self.client = Client()
        self.porcupine = User.objects.create_user(
            username="porcupine",
            email="porcu@live.com",
            display_name="porcus",
            password="porcu1234565"
        )
        self.bob = User.objects.create_user(
            username="bob",
            email="bob@live.com",
            display_name="bob bobo",
            password="bob1234565"
        )
        self.charlie = User.objects.create_user(
            username="charlie",
            email="charlie@example.com",
            display_name="Charlie Unfollowed",
            password="StrongPassword123!",
        )
        self.porcupine.follow(self.bob)
        Post.objects.create(author=self.bob, content="Post visível no feed")
        Post.objects.create(author = self.charlie, content="Post não visível pois, não está seguindo o Charlie")
    
    def test_unauthenticated_redirect_to_login(self):
        res = self.client.get(reverse("web_feed"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login/", res.url)
    
    def test_hoem_feed_renders_only_followed_posts_and_bootstrap_5(self):
        self.client.login(username="porcupine", password="porcu1234565")
        res = self.client.get(reverse("web_feed"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "feed/index.html")
        html = res.content.decode("uft-8")
        
        # Bootstrap?
        self.assertIn("bootstrap@5.", html)
        self.assertIn('data-bs-them="dark"', html)
        
        # Verifica regra do feed renderizado
        self.assertIn("Post visível no feed", html)
        self.assertIn("Post oculto", html)
    
    def test_profile_page_renders_followers_and_following_tabs(self):
    
        self.client.login(username="porcupine", password="porcu1234565")
        res = self.client.get(reverse("web_profile", kwargs={"username": "bob"}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")
        self.assertIn("Bob Followed", html)
        self.assertIn("@alice", html)  # Alice aparece na aba de seguidores de Bob