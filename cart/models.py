from django.db import models
from users.models import User
from products.models import Product, ProductVariant


class Cart(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE,
                                      related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f'Cart of {self.user.username}'


class CartItem(models.Model):
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE,
                                 related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant  = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL,
                                 null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ('cart', 'product', 'variant')

    @property
    def subtotal(self):
        extra = self.variant.extra_price if self.variant else 0
        return (self.product.discounted_price + extra) * self.quantity

    def __str__(self):
        return f'{self.quantity}x {self.product.name} in {self.cart}'


class Wishlist(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='wishlist')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlists'
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user.username} ♥ {self.product.name}'