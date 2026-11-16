from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.posts.models import Post


class FrontendTemplateTest(TestCase):
    def setUp(self):
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
        Post.objects.create(
            author=self.charlie,
            content="Post não visível pois, não está seguindo o Charlie",
        )

    def test_unauthenticated_redirect_to_login(self):
        res = self.client.get(reverse("web_feed"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login/", res.url)

    def test_home_feed_renders_only_followed_posts_and_bootstrap_5(self):
        self.client.login(username="porcupine", password="porcu1234565")
        res = self.client.get(reverse("web_feed"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "feed/index.html")
        html = res.content.decode("utf-8")

        self.assertIn("bootstrap@5.3.3", html)
        self.assertIn('data-bs-theme="dark"', html)
        self.assertIn("Post visível no feed", html)
        self.assertNotIn(
            "Post não visível pois, não está seguindo o Charlie",
            html,
        )

    def test_profile_page_renders_followers_and_following_tabs(self):
        self.client.login(username="porcupine", password="porcu1234565")
        res = self.client.get(reverse("web_profile", kwargs={"username": "bob"}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")
        self.assertIn("bob bobo", html)
        self.assertIn("@porcupine", html)
        self.assertIn("Seguidores", html)
        self.assertIn("Seguindo", html)