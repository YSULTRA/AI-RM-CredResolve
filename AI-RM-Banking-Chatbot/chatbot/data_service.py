from .models import Customer, Transaction, Investment
from django.db.models import Sum, Count, Q, Avg
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd


class DataService:
    """Service for retrieving and analyzing financial data"""

    @staticmethod
    def get_customer_context(customer_id: str) -> Dict:
        """Get comprehensive customer financial context"""
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return {}

        # Get recent transactions (last 6 months)
        six_months_ago = datetime.now().date() - timedelta(days=180)
        recent_transactions = Transaction.objects.filter(
            customer=customer,
            date__gte=six_months_ago
        ).order_by('-date')[:50]

        # Get active investments
        investments = Investment.objects.filter(customer=customer)

        # Calculate transaction summary
        transaction_summary = DataService._calculate_transaction_summary(recent_transactions)

        # Calculate investment summary
        investment_summary = DataService._calculate_investment_summary(investments)

        return {
            'customer': {
                'customer_id': customer.customer_id,
                'name': customer.name,
                'age': customer.age,
                'risk_level': customer.risk_level,
                'annual_income': float(customer.annual_income),
                'financial_goals': customer.financial_goals,
            },
            'transactions': [
                {
                    'transaction_id': t.transaction_id,
                    'date': str(t.date),
                    'category': t.category,
                    'merchant': t.merchant,
                    'amount': float(t.amount),
                    'description': t.description
                }
                for t in recent_transactions
            ],
            'investments': [
                {
                    'investment_id': i.investment_id,
                    'product_type': i.product_type,
                    'product_name': i.product_name,
                    'invested_amount': float(i.invested_amount),
                    'current_value': float(i.current_value),
                    'returns_percentage': float(i.returns_percentage),
                    'risk_level': i.risk_level
                }
                for i in investments
            ],
            'transaction_summary': transaction_summary,
            'investment_summary': investment_summary
        }

    @staticmethod
    def _calculate_transaction_summary(transactions) -> Dict:
        """Calculate transaction analytics"""
        if not transactions:
            return {}

        total_spent = sum(float(t.amount) for t in transactions)

        # Category-wise breakdown
        category_spending = {}
        for t in transactions:
            category_spending[t.category] = category_spending.get(t.category, 0) + float(t.amount)

        # Sort categories by spending
        top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]

        # Calculate monthly average
        dates = [t.date for t in transactions]
        if dates:
            months_covered = (max(dates) - min(dates)).days / 30 or 1
            monthly_average = total_spent / months_covered
        else:
            monthly_average = 0

        return {
            'total_spent': total_spent,
            'monthly_average': monthly_average,
            'top_categories': [cat[0].replace('_', ' ').title() for cat in top_categories[:3]],
            'category_breakdown': {k.replace('_', ' ').title(): v for k, v in category_spending.items()},
            'transaction_count': len(transactions)
        }

    @staticmethod
    def _calculate_investment_summary(investments) -> Dict:
        """Calculate investment analytics"""
        if not investments:
            return {}

        total_invested = sum(float(i.invested_amount) for i in investments)
        current_value = sum(float(i.current_value) for i in investments)
        total_returns = current_value - total_invested
        return_percentage = (total_returns / total_invested * 100) if total_invested > 0 else 0

        # Product type distribution
        product_types = {}
        for i in investments:
            ptype = i.product_type.replace('_', ' ').title()
            product_types[ptype] = product_types.get(ptype, 0) + 1

        # Best performing investment
        best_investment = max(investments, key=lambda x: x.returns_percentage) if investments else None

        return {
            'total_invested': total_invested,
            'current_value': current_value,
            'total_returns': total_returns,
            'return_percentage': return_percentage,
            'product_types': list(product_types.keys()),
            'investment_count': len(investments),
            'best_performer': {
                'name': best_investment.product_name,
                'return': float(best_investment.returns_percentage)
            } if best_investment else None
        }

    @staticmethod
    def query_transactions(customer_id: str, filters: Dict = None) -> List[Dict]:
        """Query transactions with filters"""
        queryset = Transaction.objects.filter(customer_id=customer_id)

        if filters:
            if 'category' in filters:
                queryset = queryset.filter(category=filters['category'])
            if 'start_date' in filters:
                queryset = queryset.filter(date__gte=filters['start_date'])
            if 'end_date' in filters:
                queryset = queryset.filter(date__lte=filters['end_date'])
            if 'min_amount' in filters:
                queryset = queryset.filter(amount__gte=filters['min_amount'])

        return [
            {
                'transaction_id': t.transaction_id,
                'date': str(t.date),
                'category': t.category,
                'merchant': t.merchant,
                'amount': float(t.amount),
                'description': t.description
            }
            for t in queryset.order_by('-date')
        ]

    @staticmethod
    def query_investments(customer_id: str, filters: Dict = None) -> List[Dict]:
        """Query investments with filters"""
        queryset = Investment.objects.filter(customer_id=customer_id)

        if filters:
            if 'product_type' in filters:
                queryset = queryset.filter(product_type=filters['product_type'])
            if 'risk_level' in filters:
                queryset = queryset.filter(risk_level=filters['risk_level'])

        return [
            {
                'investment_id': i.investment_id,
                'product_type': i.product_type,
                'product_name': i.product_name,
                'invested_amount': float(i.invested_amount),
                'current_value': float(i.current_value),
                'returns_percentage': float(i.returns_percentage),
                'returns_absolute': float(i.returns_absolute),
                'risk_level': i.risk_level
            }
            for i in queryset.order_by('-returns_percentage')
        ]

    @staticmethod
    def get_spending_by_category(customer_id: str, months: int = 6) -> Dict:
        """Get category-wise spending analysis"""
        start_date = datetime.now().date() - timedelta(days=months * 30)

        transactions = Transaction.objects.filter(
            customer_id=customer_id,
            date__gte=start_date
        )

        category_data = transactions.values('category').annotate(
            total=Sum('amount'),
            count=Count('transaction_id')
        ).order_by('-total')

        return {
            'period': f'Last {months} months',
            'categories': [
                {
                    'category': item['category'].replace('_', ' ').title(),
                    'total': float(item['total']),
                    'transaction_count': item['count']
                }
                for item in category_data
            ]
        }

    @staticmethod
    def get_portfolio_allocation(customer_id: str) -> Dict:
        """Get investment portfolio allocation"""
        investments = Investment.objects.filter(customer_id=customer_id)

        # Group by product type
        allocation = investments.values('product_type').annotate(
            total_value=Sum('current_value')
        )

        total_portfolio = sum(float(item['total_value']) for item in allocation)

        return {
            'total_value': total_portfolio,
            'allocation': [
                {
                    'product_type': item['product_type'].replace('_', ' ').title(),
                    'value': float(item['total_value']),
                    'percentage': round((float(item['total_value']) / total_portfolio * 100), 2) if total_portfolio > 0 else 0
                }
                for item in allocation
            ]
        }
