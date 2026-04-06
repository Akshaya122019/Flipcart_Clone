from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Order, OrderItem, Address
from .forms import AddressFormWithStates
from cart.models import Cart, CartItem
from payments.models import Payment


# ── helpers ───────────────────────────────────────────────
def get_cart_or_redirect(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if cart.items.count() == 0:
            return None, redirect('cart:detail')
        return cart, None
    except Cart.DoesNotExist:
        return None, redirect('cart:detail')


# ── Order list ────────────────────────────────────────────
@login_required
def order_list(request):
    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related('items').order_by('-created_at')
    return render(request, 'orders/list.html', {'orders': orders})


# ── Order detail ──────────────────────────────────────────
@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    items = order.items.select_related('product', 'variant')
    try:
        payment = order.payment
    except Exception:
        payment = None
    return render(request, 'orders/detail.html', {
        'order':   order,
        'items':   items,
        'payment': payment,
    })


# ── Cancel order ──────────────────────────────────────────
@login_required
@require_POST
def order_cancel(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    if order.status in ('pending', 'confirmed'):
        order.status = 'cancelled'
        order.save()
        # Restore stock
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save()
        messages.success(request, f'Order {order.order_number} cancelled.')
    else:
        messages.error(request, 'This order cannot be cancelled.')
    return redirect('orders:detail', pk=pk)


# ── Checkout — Step 1: Address ────────────────────────────
@login_required
def checkout(request):
    cart, redir = get_cart_or_redirect(request)
    if redir:
        messages.warning(request, 'Your cart is empty.')
        return redir

    addresses   = Address.objects.filter(user=request.user)
    address_form = AddressFormWithStates()

    if request.method == 'POST':
        action = request.POST.get('action')

        # Save new address
        if action == 'save_address':
            address_form = AddressFormWithStates(request.POST)
            if address_form.is_valid():
                addr = address_form.save(commit=False)
                addr.user = request.user
                # Set as default if first address
                if not addresses.exists():
                    addr.is_default = True
                addr.save()
                messages.success(request, 'Address saved.')
                return redirect('orders:checkout')
            # Fall through to re-render with errors

        # Select address & proceed
        elif action == 'proceed':
            address_id = request.POST.get('address_id')
            if not address_id:
                messages.error(request, 'Please select a delivery address.')
                return redirect('orders:checkout')
            request.session['checkout_address_id'] = int(address_id)
            return redirect('orders:checkout_summary')

    context = {
        'cart':         cart,
        'addresses':    addresses,
        'address_form': address_form,
    }
    return render(request, 'orders/checkout.html', context)


# ── Checkout — Step 2: Summary + Payment method ───────────
@login_required
def checkout_summary(request):
    cart, redir = get_cart_or_redirect(request)
    if redir:
        return redir

    address_id = request.session.get('checkout_address_id')
    if not address_id:
        return redirect('orders:checkout')

    address = get_object_or_404(Address, id=address_id, user=request.user)
    items   = cart.items.select_related(
                'product', 'variant'
              ).prefetch_related('product__images')

    # Calculate totals
    subtotal      = cart.total_price
    shipping_cost = 0 if subtotal >= 499 else 40
    grand_total   = subtotal + shipping_cost

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'razorpay')

        # ── Place the order ──
        order = Order.objects.create(
            user           = request.user,
            address        = address,
            payment_method = payment_method,
            total_price    = subtotal,
            shipping_cost  = shipping_cost,
            grand_total    = grand_total,
            status         = 'pending',
        )

        # Create order items + reduce stock
        for item in items:
            OrderItem.objects.create(
                order         = order,
                product       = item.product,
                variant       = item.variant,
                product_name  = item.product.name,
                product_price = item.product.discounted_price,
                quantity      = item.quantity,
                subtotal      = item.subtotal,
            )
            # Reduce stock
            product = item.product
            product.stock = max(0, product.stock - item.quantity)
            product.save()

        # Clear cart
        cart.items.all().delete()
        del request.session['checkout_address_id']

        # COD — go straight to success
        if payment_method == 'cod':
            Payment.objects.create(
                order  = order,
                user   = request.user,
                amount = grand_total,
                status = 'success',
            )
            order.status = 'confirmed'
            order.save()
            messages.success(
                request,
                f'Order {order.order_number} placed successfully!'
            )
            return redirect('orders:success', pk=order.id)

        # Razorpay — go to payment page
        return redirect('payments:razorpay_pay', order_id=order.id)

    context = {
        'cart':          cart,
        'items':         items,
        'address':       address,
        'subtotal':      subtotal,
        'shipping_cost': shipping_cost,
        'grand_total':   grand_total,
    }
    return render(request, 'orders/checkout_summary.html', context)


# ── Order success ─────────────────────────────────────────
@login_required
def order_success(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    items = order.items.select_related('product')
    return render(request, 'orders/success.html', {
        'order': order,
        'items': items,
    })