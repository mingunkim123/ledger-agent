"""accounts Admin 등록"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass
