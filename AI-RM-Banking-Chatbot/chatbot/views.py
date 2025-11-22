from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from django.db.models import Q
from .models import Customer, Transaction, Investment, ChatConversation, ChatMessage, UploadedFile
from .serializers import (
    CustomerSerializer, TransactionSerializer, InvestmentSerializer,
    ChatConversationSerializer, ChatMessageSerializer, ChatRequestSerializer,
    ChatResponseSerializer, UploadedFileSerializer, CustomerContextSerializer
)
from .gemini_service import GeminiService
from .data_service import DataService
import uuid
from datetime import datetime
import pandas as pd
import os


# Initialize services
gemini_service = GeminiService()
data_service = DataService()


def chat_interface(request):
    """Render the chat UI"""
    customers = Customer.objects.all()
    return render(request, 'chatbot/chat_interface.html', {'customers': customers})


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer CRUD operations"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    lookup_field = 'customer_id'


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for Transaction operations"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        queryset = Transaction.objects.all()
        customer_id = self.request.query_params.get('customer_id')
        category = self.request.query_params.get('category')

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if category:
            queryset = queryset.filter(category=category)

        return queryset.order_by('-date')


class InvestmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Investment operations"""
    queryset = Investment.objects.all()
    serializer_class = InvestmentSerializer

    def get_queryset(self):
        queryset = Investment.objects.all()
        customer_id = self.request.query_params.get('customer_id')

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        return queryset.order_by('-returns_percentage')


class ChatAPIView(APIView):
    """Main Chat API endpoint"""

    def post(self, request):
        """Handle chat requests with context-aware responses"""
        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer_id = serializer.validated_data['customer_id']
        user_message = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')

        try:
            # Verify customer exists
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create conversation
        if conversation_id:
            try:
                conversation = ChatConversation.objects.get(
                    conversation_id=conversation_id,
                    customer=customer
                )
            except ChatConversation.DoesNotExist:
                conversation = self._create_new_conversation(customer)
        else:
            conversation = self._create_new_conversation(customer)

        # Save user message
        user_msg = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )

        # Get conversation history
        conversation_history = self._get_conversation_history(conversation)

        # Classify intent
        intent = gemini_service.classify_intent(user_message)

        # Get customer financial context
        context_data = data_service.get_customer_context(customer_id)

        # Get previous thought signature if exists
        previous_thought = None
        if conversation_history:
            last_assistant_msg = next(
                (msg for msg in reversed(conversation_history) if msg['role'] == 'assistant'),
                None
            )
            if last_assistant_msg:
                previous_thought = last_assistant_msg.get('thought_signature')

        # Generate AI response
        ai_response = gemini_service.generate_response(
            user_query=user_message,
            customer_profile=context_data['customer'],
            context_data=context_data,
            conversation_history=conversation_history,
            previous_thought_signature=previous_thought
        )

        # Save assistant message with thought signature
        assistant_msg = ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response['response'],
            intent=intent,
            data_sources=['transactions', 'investments', 'customer_profile'],
            thought_signature=ai_response.get('thought_signature')
        )

        # Generate follow-up suggestions
        suggestions = gemini_service.generate_follow_up_suggestions(intent)

        response_data = {
            'conversation_id': conversation.conversation_id,
            'response': ai_response['response'],
            'intent': intent,
            'suggestions': suggestions,
            'data_context': {
                'transaction_count': len(context_data.get('transactions', [])),
                'investment_count': len(context_data.get('investments', [])),
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _create_new_conversation(self, customer):
        """Create a new conversation"""
        return ChatConversation.objects.create(
            conversation_id=str(uuid.uuid4()),
            customer=customer
        )

    def _get_conversation_history(self, conversation):
        """Get conversation history as list"""
        messages = ChatMessage.objects.filter(
            conversation=conversation
        ).order_by('timestamp')

        return [
            {
                'role': msg.role,
                'content': msg.content,
                'thought_signature': msg.thought_signature,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in messages
        ]


@api_view(['GET'])
def get_customer_context(request, customer_id):
    """Get comprehensive customer context"""
    try:
        context = data_service.get_customer_context(customer_id)
        return Response(context, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_conversation_history(request, conversation_id):
    """Get conversation history"""
    try:
        conversation = ChatConversation.objects.get(conversation_id=conversation_id)
        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except ChatConversation.DoesNotExist:
        return Response(
            {'error': 'Conversation not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def upload_file(request):
    """Upload and process CSV files"""
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    file = request.FILES['file']
    file_type = request.POST.get('file_type')
    customer_id = request.POST.get('customer_id')

    if not file_type or not customer_id:
        return Response(
            {'error': 'file_type and customer_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Save uploaded file
    uploaded_file = UploadedFile.objects.create(
        file_name=file.name,
        file_type=file_type,
        file_path=file,
        uploaded_by=customer
    )

    # Process file based on type
    try:
        records_imported = process_uploaded_file(uploaded_file, customer)
        uploaded_file.processed = True
        uploaded_file.records_imported = records_imported
        uploaded_file.save()

        return Response({
            'message': 'File uploaded and processed successfully',
            'records_imported': records_imported
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Error processing file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def process_uploaded_file(uploaded_file, customer):
    """Process uploaded CSV file and import data"""
    file_path = uploaded_file.file_path.path
    df = pd.read_csv(file_path)
    records_imported = 0

    if uploaded_file.file_type == 'transaction':
        for _, row in df.iterrows():
            Transaction.objects.get_or_create(
                transaction_id=row['transaction_id'],
                defaults={
                    'customer': customer,
                    'date': row['date'],
                    'category': row['category'],
                    'merchant': row['merchant'],
                    'amount': row['amount'],
                    'payment_method': row.get('payment_method', 'upi'),
                    'description': row.get('description', '')
                }
            )
            records_imported += 1

    elif uploaded_file.file_type == 'investment':
        for _, row in df.iterrows():
            Investment.objects.get_or_create(
                investment_id=row['investment_id'],
                defaults={
                    'customer': customer,
                    'product_type': row['product_type'],
                    'product_name': row['product_name'],
                    'purchase_date': row['purchase_date'],
                    'invested_amount': row['invested_amount'],
                    'current_value': row['current_value'],
                    'units': row.get('units', 0),
                    'purchase_nav': row.get('purchase_nav', 0),
                    'current_nav': row.get('current_nav', 0),
                    'returns_absolute': row['returns_absolute'],
                    'returns_percentage': row['returns_percentage'],
                    'risk_level': row['risk_level']
                }
            )
            records_imported += 1

    return records_imported