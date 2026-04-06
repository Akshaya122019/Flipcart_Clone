from django.db import models
from users.models import User
from products.models import Product, ProductVariant


class Address(models.Model):
    ADDRESS_TYPES = (
        ('home',   'Home'),
        ('work',   'Work'),
        ('other',  'Other'),
    )
    user         = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='addresses')
    full_name    = models.CharField(max_length=255)
    phone        = models.CharField(max_length=15)
    line1        = models.CharField(max_length=255)
    line2        = models.CharField(max_length=255, blank=True)
    city         = models.CharField(max_length=100)
    state        = models.CharField(max_length=100)
    pincode      = models.CharField(max_length=10)
    country      = models.CharField(max_length=100, default='India')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES,
                                    default='home')
    is_default   = models.BooleanField(default=False)

    class Meta:
        db_table  = 'addresses'
        ordering  = ['-is_default']
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f'{self.full_name}, {self.city} — {self.pincode}'


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
        ('returned',   'Returned'),
        ('refunded',   'Refunded'),
    )
    PAYMENT_METHODS = (
        ('razorpay', 'Razorpay'),
        ('cod',      'Cash on Delivery'),
    )

    user           = models.ForeignKey(User, on_delete=models.CASCADE,
                                       related_name='orders')
    address        = models.ForeignKey(Address, on_delete=models.SET_NULL,
                                       null=True)
    order_number   = models.CharField(max_length=20, unique=True)
    status         = models.CharField(max_length=15, choices=STATUS_CHOICES,
                                      default='pending')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS,
                                      default='razorpay')
    total_price    = models.DecimalField(max_digits=10, decimal_places=2)
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost  = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    grand_total    = models.DecimalField(max_digits=10, decimal_places=2)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = 'FK' + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order {self.order_number} by {self.user.username}'


class OrderItem(models.Model):
    order       = models.ForeignKey(Order, on_delete=models.CASCADE,
                                    related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.SET_NULL,
                                    null=True)
    variant     = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL,
                                    null=True, blank=True)
    product_name  = models.CharField(max_length=300)   # snapshot at order time
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity      = models.PositiveIntegerField(default=1)
    subtotal      = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f'{self.quantity}x {self.product_name} in {self.order.order_number}'