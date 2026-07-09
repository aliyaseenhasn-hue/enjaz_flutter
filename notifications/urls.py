from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notifications'),
    path('unread/', views.UnreadCountView.as_view(), name='unread-count'),
    path('read-all/', views.MarkReadView.as_view(), name='mark-all-read'),
    path('<int:pk>/read/', views.MarkReadView.as_view(), name='mark-read'),
]
