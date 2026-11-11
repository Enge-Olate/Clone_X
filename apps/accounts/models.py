from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel
# Create your models here.

class User(AbstractUser, TimeStampedModel):
    username = models.CharField(unique=True, max_length=80)
    email = models.EmailField(unique=True, db_index=True)
    bio = models.CharField(max_length=160, blank=True, default="")
    avatar = models.ImageField(
        upload_to="",
        
        null=True,
        blank=True,
        validators=["jpeg", "gif", "png", "jpg"]
    )
    following = models.ManyToManyField(
        through="Follow",
        symmetrical=False,
        related_name="followers",
        verbose_name="Seguindo"
    )
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["-created_at"]

    def __str__(self)-> str:
        return super().__str__(self.username)
    
    def follow(self, target_user: "User") -> tuple["Follow", bool]:
        if self == target_user:
            raise ValidationError("Um usuário não pode seguir a si mesmo.")
        return Follow.objects.filter(
            following = target_user
        )
    
    def unfollow(self, target_user: "User") -> int:
        deleted_count, _ =Follow.objects.filter(
            followers = self,
            following = target_user
        ).delete()
        return deleted_count
    
    def is_following(self, taret_user: "User")-> bool:
        if not self.is_authenticated:
            return False
        return Follow.objects.filter(
            followers = self,
            following = taret_user
        ).exists()
    
    @property
    def followers_count(self) -> int:
        return self.followers_relations.count()
    
    @property
    def following_count(self) -> int:
        return self.following_relations.count()
    
class Follow(TimeStampedModel):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following_relations",
        verbose_name="Seguidor",
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers_relations",
        verbose_name="Seguindo",
    )

    class Meta:
        verbose_name = "Vínculo de Seguir"
        verbose_name_plural = "Vínculos de Seguir"
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_user_follow",
            ),
            models.CheckConstraint(
                check=~Q(follower=F("following")),
                name="prevent_self_follow",
            ),
        ]

    def clean(self) -> None:
        if self.follower_id == self.following_id:
            raise ValidationError("Você não pode seguir a sua própria conta.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"@{self.follower.username} -> @{self.following.username}"