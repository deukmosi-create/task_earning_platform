from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Plan, PlanUpgrade
from .serializers import PlanSerializer, PlanUpgradeRequestSerializer
from apps.wallets.models import Wallet, Transaction
from apps.notifications.utils import send_notification
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plan_list_view(request):
    plans = Plan.objects.filter(is_active=True)
    serializer = PlanSerializer(plans, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upgrade_plan_view(request):
    serializer = PlanUpgradeRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            new_plan = Plan.objects.get(id=serializer.validated_data['plan_id'])
            user = request.user
            
            if user.plan == new_plan.name:
                return Response({'error': 'You are already on this plan'}, status=status.HTTP_400_BAD_REQUEST)
            
            if new_plan.priority <= Plan.objects.get(name=user.plan).priority:
                return Response({'error': 'Cannot downgrade to a lower priority plan'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user has sufficient balance
            wallet, created = Wallet.objects.get_or_create(user=user)
            if wallet.balance < new_plan.monthly_price:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Process payment
            Transaction.objects.create(
                wallet=wallet,
                amount=new_plan.monthly_price,
                transaction_type='plan_upgrade',
                description=f'Plan upgrade from {user.plan} to {new_plan.name}',
                reference=f'upgrade_{user.id}'
            )
            
            # Update user plan
            old_plan = user.plan
            user.plan = new_plan.name
            user.save()
            
            # Record upgrade
            PlanUpgrade.objects.create(
                user=user,
                old_plan=old_plan,
                new_plan=new_plan.name,
                upgrade_cost=new_plan.monthly_price,
                payment_method=serializer.validated_data['payment_method'],
                transaction_id=f'upgrade_{user.id}_{new_plan.id}'
            )
            
            # Send notification
            send_notification(
                user=user,
                title='Plan Upgraded',
                message=f'Your plan has been upgraded to {new_plan.name}',
                notification_type='plan_upgrade'
            )
            
            return Response({'message': 'Plan upgraded successfully', 'new_plan': new_plan.name})
        
        except Plan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_plan_view(request):
    plan = Plan.objects.get(name=request.user.plan)
    serializer = PlanSerializer(plan)
    return Response(serializer.data)