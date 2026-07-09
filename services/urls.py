"""
services/urls.py
مسارات API الخدمات — مرتّبة حسب المنطق
"""

from django.urls import path
from . import views

urlpatterns = [

    # ── التصنيفات ─────────────────────────────────────────────────
    path('categories/', views.CategoryListView.as_view(), name='categories'),

    # ── طلبات الخدمة (الزبون) ────────────────────────────────────
    path('requests/',                   views.ServiceRequestCreateView.as_view(), name='request-create'),
    path('requests/my/',                views.MyRequestsView.as_view(),           name='my-requests'),
    path('requests/<int:pk>/',          views.ServiceRequestDetailView.as_view(), name='request-detail'),
    path('requests/<int:pk>/cancel/',   views.CancelRequestView.as_view(),        name='request-cancel'),
    path('requests/<int:pk>/review/',   views.SubmitReviewView.as_view(),         name='request-review'),
    path('requests/<int:pk>/messages/', views.RequestMessagesView.as_view(),      name='request-messages'),

    # ── طلبات الخدمة (المهني) ────────────────────────────────────
    path('agent/available/',         views.AvailableRequestsForAgentView.as_view(),   name='available-requests'),
    path('agent/accept/<int:pk>/',   views.AcceptRequestView.as_view(),               name='accept-request'),
    path('agent/update/<int:pk>/',   views.UpdateRequestStatusView.as_view(),         name='update-status'),
    path('agent/reject/<int:pk>/',   views.RejectRequestView.as_view(),               name='agent-reject-request'),

    # ── المحادثات ─────────────────────────────────────────────────
    path('chat/conversations/', views.ChatConversationsView.as_view(), name='chat-conversations'),

    # ── المهنيون حسب القرب ─────────────────────────────────────────
    path('agents/nearby/', views.NearbyAgentsView.as_view(), name='nearby-agents'),

    # ── المحفظة ───────────────────────────────────────────────────
    path('wallet/',              views.WalletInfoView.as_view(),         name='wallet-info'),
    path('wallet/deposit/',      views.WalletDepositView.as_view(),      name='wallet-deposit'),
    path('wallet/withdraw/',     views.WalletWithdrawView.as_view(),     name='wallet-withdraw'),
    path('wallet/transactions/', views.WalletTransactionsView.as_view(), name='wallet-transactions'),

    # ── الإدارة ───────────────────────────────────────────────────
    path('admin/requests/',                  views.AdminRequestListView.as_view(), name='admin-requests'),
    path('admin/requests/<int:pk>/assign/',  views.AdminAssignAgentView.as_view(), name='admin-assign'),
    path('admin/stats/',                     views.AdminStatsView.as_view(),       name='admin-stats'),
]