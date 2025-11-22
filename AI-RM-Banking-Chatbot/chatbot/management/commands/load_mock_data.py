from django.core.management.base import BaseCommand
from chatbot.models import Customer, Transaction, Investment
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Load mock data from CSV files'

    def handle(self, *args, **options):
        base_path = 'mock_data/'

        # Load customers
        self.stdout.write('Loading customers...')
        customers_df = pd.read_csv(f'{base_path}customer_profiles.csv')
        for _, row in customers_df.iterrows():
            Customer.objects.get_or_create(
                customer_id=row['customer_id'],
                defaults={
                    'name': row['name'],
                    'age': row['age'],
                    'risk_level': row['risk_level'],
                    'annual_income': row['annual_income'],
                    'financial_goals': row['financial_goals'],
                    'account_opening_date': row['account_opening_date'],
                    'email': row['email'],
                    'phone': str(row['phone'])
                }
            )
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(customers_df)} customers'))

        # Load transactions
        self.stdout.write('Loading transactions...')
        transactions_df = pd.read_csv(f'{base_path}transactions.csv')
        for _, row in transactions_df.iterrows():
            Transaction.objects.get_or_create(
                transaction_id=row['transaction_id'],
                defaults={
                    'customer_id': row['customer_id'],
                    'date': row['date'],
                    'category': row['category'],
                    'merchant': row['merchant'],
                    'amount': row['amount'],
                    'payment_method': row['payment_method'],
                    'description': row['description']
                }
            )
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(transactions_df)} transactions'))

        # Load investments
        self.stdout.write('Loading investments...')
        investments_df = pd.read_csv(f'{base_path}investments.csv')
        for _, row in investments_df.iterrows():
            Investment.objects.get_or_create(
                investment_id=row['investment_id'],
                defaults={
                    'customer_id': row['customer_id'],
                    'product_type': row['product_type'],
                    'product_name': row['product_name'],
                    'purchase_date': row['purchase_date'],
                    'invested_amount': row['invested_amount'],
                    'current_value': row['current_value'],
                    'units': row['units'],
                    'purchase_nav': row['purchase_nav'],
                    'current_nav': row['current_nav'],
                    'returns_absolute': row['returns_absolute'],
                    'returns_percentage': row['returns_percentage'],
                    'risk_level': row['risk_level']
                }
            )
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(investments_df)} investments'))

        self.stdout.write(self.style.SUCCESS('\n🎉 All mock data loaded successfully!'))
