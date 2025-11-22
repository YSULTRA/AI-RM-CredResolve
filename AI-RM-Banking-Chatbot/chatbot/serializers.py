from rest_framework import serializers
from .models import Customer, Transaction, Investment, ChatConversation, ChatMessage, UploadedFile


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model"""
    class Meta:
        model = Customer
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'


class InvestmentSerializer(serializers.ModelSerializer):
    """Serializer for Investment model"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Investment
        fields = '__all__'


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for Chat messages"""
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'timestamp', 'intent', 'data_sources']
        read_only_fields = ['timestamp']


class ChatConversationSerializer(serializers.ModelSerializer):
    """Serializer for Chat conversations with messages"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = ChatConversation
        fields = ['conversation_id', 'customer', 'customer_name', 'started_at', 
                  'last_activity', 'is_active', 'messages']
        read_only_fields = ['started_at', 'last_activity']


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for incoming chat requests"""
    customer_id = serializers.CharField(required=True)
    message = serializers.CharField(required=True)
    conversation_id = serializers.CharField(required=False, allow_null=True)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat responses"""
    conversation_id = serializers.CharField()
    response = serializers.CharField()
    data_context = serializers.JSONField(required=False)
    intent = serializers.CharField(required=False)
    suggestions = serializers.ListField(child=serializers.CharField(), required=False)


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for file uploads"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.name', read_only=True)

    class Meta:
        model = UploadedFile
        fields = '__all__'
        read_only_fields = ['uploaded_at', 'processed', 'records_imported']


class CustomerContextSerializer(serializers.Serializer):
    """Serializer for customer financial context"""
    customer_info = CustomerSerializer()
    recent_transactions = TransactionSerializer(many=True)
    active_investments = InvestmentSerializer(many=True)
    financial_summary = serializers.JSONField()
