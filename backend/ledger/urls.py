"""ledger 앱 URL 라우팅"""

from django.urls import path

from ledger.views import (
    ChatView,
    SummaryView,
    TransactionListCreateView,
    UndoView,
)

app_name = "ledger"

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("transactions/", TransactionListCreateView.as_view(), name="transactions"),
    path("undo/", UndoView.as_view(), name="undo"),
    path("summary/", SummaryView.as_view(), name="summary"),
]
