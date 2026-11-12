from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only = True,
        required = True,
        validators = [validate_password],
        style = {"input_type":"password"},
    )
    password_confirm = serializers.CharField(
        write_only = True,
        required = True,
        style = {"input_type": "password"}
    )
    class Meta:
        model = User
        fields =  [
            "id",
            "username",
            "email",
            "bio",
            "avatar",
            "password",
            "password_confirm",
        ]
    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("passoword_confirm"):
            raise serializers.ValidationsError({
                "password_confirm": "As senhas informadas não coincidem."
            })
        return attrs
    
    def create(self, validate_data: dict) -> User:
        return User.objects.create_user(**validate_data)

class UserPublicSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "bio",
            "avatar",
            "followers_count",
            "following_count",
            "is_following",
            "created_at",
        ]

    def get_is_following(self, obj: User) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.is_following(obj)
        return False

class ProfileUpdateSerializer(serializers.ModelSerializer):
    
    display_name = serializers.CharField(max_length=80, required=False, allow_blank=False)
    bio = serializers.CharField(max_length=160, required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False, allow_null=True)
    current_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "display_name",
            "bio",
            "avatar",
            "current_password",
            "new_password",
        ]

    def validate(self, attrs: dict) -> dict:
        new_password = attrs.get("new_password")
        current_password = attrs.get("current_password")

        if new_password:
            if not current_password:
                raise serializers.ValidationError(
                    {"current_password": "Informe sua senha atual para definir uma nova senha."}
                )
            if not self.instance.check_password(current_password):
                raise serializers.ValidationError(
                    {"current_password": "A senha atual informada está incorreta."}
                )
            validate_password(new_password, self.instance)
        return attrs

    def update(self, instance: User, validated_data: dict) -> CustomUser:
        validated_data.pop("current_password", None)
        new_password = validated_data.pop("new_password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if new_password:
            instance.set_password(new_password)

        instance.save()

        request = self.context.get("request")
        if new_password and request:
            update_session_auth_hash(request, instance)

        return instance