from django.contrib import admin
from .models import Address, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('order_number', 'user', 'status', 'grand_total', 'created_at')
    list_filter   = ('status', 'payment_method')
    search_fields = ('order_number', 'user__email')
    inlines       = [OrderItemInline]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'state', 'is_default')