from django.contrib import admin
from .models import Customer, Transaction, Investment, ChatConversation, ChatMessage, UploadedFile

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'name', 'age', 'risk_level', 'annual_income']
    search_fields = ['customer_id', 'name', 'email']
    list_filter = ['risk_level', 'financial_goals']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'customer', 'date', 'category', 'merchant', 'amount']
    search_fields = ['transaction_id', 'merchant']
    list_filter = ['category', 'payment_method', 'date']
    date_hierarchy = 'date'

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['investment_id', 'customer', 'product_name', 'invested_amount', 'current_value', 'returns_percentage']
    search_fields = ['investment_id', 'product_name']
    list_filter = ['product_type', 'risk_level']

@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_id', 'customer', 'started_at', 'last_activity', 'is_active']
    search_fields = ['conversation_id', 'customer__name']
    list_filter = ['is_active', 'started_at']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'content_preview', 'timestamp', 'intent']
    search_fields = ['content']
    list_filter = ['role', 'intent', 'timestamp']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'file_type', 'uploaded_by', 'uploaded_at', 'processed', 'records_imported']
    list_filter = ['file_type', 'processed', 'uploaded_at']
    search_fields = ['file_name']
