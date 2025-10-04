from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    serializer = WalletSerializer(wallet)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_history_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = Transaction.objects.filter(wallet=wallet)
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def balance_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    return Response({'balance': float(wallet.balance)})