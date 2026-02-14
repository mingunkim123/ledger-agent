"""커스텀 User 모델"""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    커스텀 유저 모델.

    현재는 AbstractUser를 그대로 사용하지만,
    추후 phone, profile_image 등 필드 확장 가능.
    """

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username
