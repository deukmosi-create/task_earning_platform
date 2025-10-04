from django.db import models
from apps.users.models import User

class ReferralLink(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s referral link"

class ReferralBonus(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.ForeignKey('payments.Deposit', on_delete=models.CASCADE, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.referrer.username} referred {self.referee.username} - ${self.amount}"

class ReferralStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_referrals = models.IntegerField(default=0)
    total_bonus_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Referral Stats"