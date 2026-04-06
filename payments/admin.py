from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = (
        'order', 'user', 'amount', 'status',
        'razorpay_payment_id', 'created_at'
    )
    list_filter   = ('status',)
    search_fields = (
        'order__order_number',
        'user__email',
        'razorpay_payment_id',
        'razorpay_order_id',
    )
    readonly_fields = (
        'razorpay_order_id',
        'razorpay_payment_id',
        'razorpay_signature',
        'created_at',
        'updated_at',
    )