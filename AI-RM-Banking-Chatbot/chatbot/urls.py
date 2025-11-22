from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'investments', views.InvestmentViewSet, basename='investment')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),

    # Chat endpoints
    path('api/chat/', views.ChatAPIView.as_view(), name='chat'),
    path('api/context/<str:customer_id>/', views.get_customer_context, name='customer-context'),
    path('api/conversation/<str:conversation_id>/', views.get_conversation_history, name='conversation-history'),

    # File upload
    path('api/upload/', views.upload_file, name='upload-file'),

    # UI
    path('', views.chat_interface, name='chat-interface'),
]
