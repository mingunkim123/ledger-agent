from .settings import *

# 테스트는 SQLite 사용 (속도 + 권한 문제 해결)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# 비밀번호 해싱 속도 향상 (테스트 시간 단축)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Celery 등 비동기 작업 동기 실행 (필요시)
CELERY_TASK_ALWAYS_EAGER = True
