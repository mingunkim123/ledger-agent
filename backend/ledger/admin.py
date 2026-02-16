from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = [
        "occurred_date",
        "type",
        "amount",
        "category",
        "subcategory",
        "memo",
    ]
    list_filter = ["type", "category", "occurred_date"]
    search_fields = ["memo", "merchant", "category", "subcategory"]
