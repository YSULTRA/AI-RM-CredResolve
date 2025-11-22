from django.db import models
from django.contrib.auth.models import User
import json

class Customer(models.Model):
    """Customer profile model"""
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]

    customer_id = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    age = models.IntegerField()
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2)
    financial_goals = models.CharField(max_length=200)
    account_opening_date = models.DateField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_id} - {self.name}"


class Transaction(models.Model):
    """Transaction model"""
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
    ]

    transaction_id = models.CharField(max_length=20, unique=True, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    category = models.CharField(max_length=50)
    merchant = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['customer', 'date']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.merchant} - ₹{self.amount}"


class Investment(models.Model):
    """Investment model"""
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]

    investment_id = models.CharField(max_length=20, unique=True, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='investments')
    product_type = models.CharField(max_length=50)
    product_name = models.CharField(max_length=200)
    purchase_date = models.DateField()
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    units = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    purchase_nav = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_nav = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    returns_absolute = models.DecimalField(max_digits=12, decimal_places=2)
    returns_percentage = models.DecimalField(max_digits=8, decimal_places=2)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments'
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['customer', 'product_type']),
        ]

    def __str__(self):
        return f"{self.investment_id} - {self.product_name}"


class ChatConversation(models.Model):
    """Chat conversation model to track sessions"""
    conversation_id = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='conversations')
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'chat_conversations'
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.conversation_id} - {self.customer.name}"


class ChatMessage(models.Model):
    """Individual chat messages with context"""
    ROLES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Metadata for context
    intent = models.CharField(max_length=100, blank=True, null=True)
    data_sources = models.JSONField(default=list, blank=True)  # Track what data was used
    thought_signature = models.TextField(blank=True, null=True)  # Gemini 3 thought signature

    class Meta:
        db_table = 'chat_messages'
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class UploadedFile(models.Model):
    """Track uploaded files for RAG"""
    FILE_TYPES = [
        ('transaction', 'Transaction Data'),
        ('investment', 'Investment Data'),
        ('customer', 'Customer Data'),
        ('document', 'Document'),
    ]

    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_path = models.FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    records_imported = models.IntegerField(default=0)

    class Meta:
        db_table = 'uploaded_files'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} - {self.file_type}"
