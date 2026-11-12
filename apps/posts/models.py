from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.core.validators import validate_image_size_and_extension
# Create your models here.

class Post(TimeStampedModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Autor",
    )
    content = models.CharField(
        "Conteúdo",
        max_length=280
    )
    image = models.ImageField(
        upload_to="posts",
        blank=True,
        null=True,
        validators=[
            validate_image_size_and_extension
        ]
    )
    
    
    class Meta:
        verbose_name = "Postagem"
        verbose_name_plural = "Postagens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["author", "-created_at"],
                name="idx_post_author_created"
            )
        ]
    
    def __str__(self) -> str:
        return f"@{self.author.username}: {self.content[:40]}"

    def toggle_like(self, user) -> tuple[bool, int]:
        
        existing = self.likes.filter(user=user).first()
        if existing:
            existing.delete()
            return False, self.likes.count()
        Like.objects.create(post=self, user=user)
        return True, self.likes.count()

class Like(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="Usuário",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="Postagem",
    )
    
    class Meta:
        verbose_name = "Curtida"
        verbose_name_plural = "Curtidas"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_post_like_per_user"
            )
        ]
        
    def __str__(self) -> str:
        return f"@{self.user.username} curtiu {self.post_id}"
    
class Comment(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Postagem",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Autor",
    )
    content = models.CharField("Comentário", max_length=280)

    class Meta:
        verbose_name = "Comentário"
        verbose_name_plural = "Comentários"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Comentário de @{self.author.username} em {self.post_id}"