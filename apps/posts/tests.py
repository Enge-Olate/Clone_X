from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from .models import Post, Comment
# Create your tests here.
class PostAndFeedBackendTestCase(APITestCase):
    def setUp(self):
        self.porcupine = User.objects.create_user(
            username="porcupine",
            email="porcu@live.com",
            display_name = "@porcus",
            password="porcus1234",
        )
        self.bob = User.objects.create_user(
            username="bob",
            email="bob@gmail.com",
            display_name = "bob",
            password="bobonco1234",
        )
        
        self.stranger = User.objects.create_user(
            username="stranger",
            email="stranger@example.com",
            display_name="Stranger (Não Seguido)",
            password="StrongPassword123!",
        )
        self.porcupine.follow(self.bob)
        self.bob_post = Post.objects.create(
            author = self.bob,
            content = "Postagem do onco Bob."
        )
        self.stranger_post = Post.objects.create(
            author = self.stranger, 
            content="Postagem de quem porcupine não segue."
        )
    def test_feed_display_only_followed_user_posts(self):
        self.client.force_authenticate(user=self.porcupine)
        response = self.client.get("/api/v1/posts/feed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.bob_post.id)
        self.assertEqual(results[0]["author"]["username"], "bob")
        post_ids = [post["id"] for post in response.data["results"]]
        self.assertIn(self.bob_post.id, post_ids)
        self.assertNotIn(self.stranger_post.id, post_ids)
        
    def test_like_and_comment_interactions(self):
        self.client.force_authenticate(user=self.porcupine)

        like_res = self.client.post(f"/api/v1/posts/{self.bob_post.id}/like/")
        self.assertEqual(like_res.status_code, status.HTTP_200_OK)
        self.assertTrue(like_res.data["liked"])
        self.assertEqual(like_res.data["likes_count"], 1)

        unlike_res = self.client.post(f"/api/v1/posts/{self.bob_post.id}/like/")
        self.assertFalse(unlike_res.data["liked"])
        self.assertEqual(unlike_res.data["likes_count"], 0)

        comment_res = self.client.post(
            f"/api/v1/posts/{self.bob_post.id}/comments/",
            {"content": "Excelente arquitetura, Bob!"},
            format="json",
        )
        self.assertEqual(comment_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.filter(post=self.bob_post).count(), 1)
        

    def test_only_author_can_delete_post(self):
        self.client.force_authenticate(user=self.porcupine)
        forbidden_res = self.client.delete(f"/api/v1/posts/{self.bob_post.id}/")
        self.assertEqual(forbidden_res.status_code, status.HTTP_403_FORBIDDEN)
        