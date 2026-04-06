from django.db import models
from users.models import User
from orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = (
        ('created',  'Created'),
        ('pending',  'Pending'),
        ('success',  'Success'),
        ('failed',   'Failed'),
        ('refunded', 'Refunded'),
    )

    order          = models.OneToOneField(Order, on_delete=models.CASCADE,
                                          related_name='payment')
    user           = models.ForeignKey(User, on_delete=models.CASCADE,
                                       related_name='payments')
    razorpay_order_id   = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature  = models.CharField(max_length=200, blank=True)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    status         = models.CharField(max_length=15, choices=STATUS_CHOICES,
                                      default='created')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment {self.razorpay_payment_id or "pending"} — {self.status}'