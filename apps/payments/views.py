from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import Deposit, Withdrawal, PaymentMethod
from .serializers import CreateDepositSerializer, CreateWithdrawalSerializer, PaymentMethodSerializer
from apps.wallets.models import Wallet, Transaction
from apps.referrals.models import ReferralBonus
from apps.notifications.utils import send_notification
import stripe
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_deposit_view(request):
    serializer = CreateDepositSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        
        if amount <= 0:
            return Response({'error': 'Amount must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create deposit record
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            payment_method=payment_method,
            transaction_id=f'dep_{request.user.id}_{timezone.now().timestamp()}',
            status='pending'
        )
        
        # Process payment based on method
        if payment_method == 'stripe':
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100),  # Stripe uses cents
                    currency='usd',
                    metadata={'deposit_id': deposit.id}
                )
                
                return Response({
                    'client_secret': intent.client_secret,
                    'deposit_id': deposit.id
                })
            except stripe.error.StripeError as e:
                deposit.status = 'failed'
                deposit.save()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': 'Deposit created successfully',
            'deposit_id': deposit.id,
            'status': deposit.status
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def webhook_stripe_view(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return Response({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return Response({'error': 'Invalid signature'}, status=400)
    
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        deposit_id = intent['metadata'].get('deposit_id')
        
        try:
            deposit = Deposit.objects.get(id=deposit_id)
            deposit.status = 'completed'
            deposit.save()
            
            # Add to wallet
            wallet, created = Wallet.objects.get_or_create(user=deposit.user)
            Transaction.objects.create(
                wallet=wallet,
                amount=deposit.amount,
                transaction_type='deposit',
                description='Deposit via Stripe',
                reference=deposit.transaction_id
            )
            
            # Update user deposit total
            deposit.user.total_deposits += deposit.amount
            deposit.user.save()
            
            # Process referral bonus if applicable
            if deposit.user.referred_by:
                ReferralBonus.objects.create(
                    referrer=deposit.user.referred_by,
                    referee=deposit.user,
                    amount=deposit.amount * 0.1,  # 10% referral bonus
                    deposit=deposit
                )
            
            send_notification(
                user=deposit.user,
                title='Deposit Completed',
                message=f'Your deposit of ${deposit.amount} has been completed successfully',
                notification_type='deposit_completed'
            )
            
        except Deposit.DoesNotExist:
            logger.error(f'Deposit with ID {deposit_id} not found')
    
    return Response({'status': 'success'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_withdrawal_view(request):
    serializer = CreateWithdrawalSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        payment_method_id = serializer.validated_data['payment_method_id']
        account_details = serializer.validated_data['account_details']
        
        # Check if user has sufficient balance
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        if wallet.balance < amount:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if withdrawal amount meets minimum
        if amount < 10:  # Minimum withdrawal amount
            return Response({'error': 'Minimum withdrawal amount is $10'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment_method = PaymentMethod.objects.get(
                id=payment_method_id,
                user=request.user,
                is_verified=True
            )
        except PaymentMethod.DoesNotExist:
            return Response({'error': 'Invalid payment method'}, status=status.HTTP_400_BAD_REQUEST)
        
        withdrawal = Withdrawal.objects.create(
            user=request.user,
            amount=amount,
            payment_method=payment_method.method_type,
            account_details=account_details,
            transaction_id=f'wd_{request.user.id}_{timezone.now().timestamp()}',
            status='pending'
        )
        
        return Response({
            'message': 'Withdrawal request submitted',
            'withdrawal_id': withdrawal.id,
            'status': withdrawal.status
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_payment_methods_view(request):
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    serializer = PaymentMethodSerializer(payment_methods, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_payment_method_view(request):
    method_type = request.data.get('method_type')
    details = request.data.get('details')
    
    if not method_type or not details:
        return Response({'error': 'Method type and details are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    payment_method = PaymentMethod.objects.create(
        user=request.user,
        method_type=method_type,
        details=details,
        is_verified=False
    )
    
    return Response({
        'message': 'Payment method added',
        'method_id': payment_method.id,
        'is_verified': payment_method.is_verified
    })