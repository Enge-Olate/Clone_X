from django.core.exceptions import ValidationError


def validate_image_size_and_extension(image) -> None:
    """Valida se a imagem enviada não excede 5MB e possui extensão segura."""
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"O tamanho máximo permitido para a imagem é {max_size_mb}MB.")
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp", ".gif")
    if not image.name.lower().endswith(valid_extensions):
        raise ValidationError("Formato de imagem inválido. Utilize JPG, PNG, WEBP ou GIF.")