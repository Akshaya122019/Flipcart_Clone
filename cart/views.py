from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages

from products.models import Product, ProductVariant
from .models import Cart, CartItem, Wishlist


# ── Helper: get or create cart ────────────────────────────
def get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# ── Cart detail page ──────────────────────────────────────
@login_required
def cart_detail(request):
    cart  = get_cart(request.user)
    items = cart.items.select_related(
                'product', 'variant'
            ).prefetch_related('product__images')
    context = {
        'cart':  cart,
        'items': items,
    }
    return render(request, 'cart/detail.html', context)


# ── Add to cart (AJAX POST) ───────────────────────────────
@login_required
@require_POST
def cart_add(request):
    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')
    quantity   = int(request.POST.get('quantity', 1))

    product = get_object_or_404(Product, id=product_id, is_active=True)

    if product.stock < 1:
        return JsonResponse({
            'success': False,
            'message': 'This product is out of stock.'
        })

    cart    = get_cart(request.user)
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)

    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, variant=variant,
        defaults={'quantity': quantity}
    )

    if not created:
        item.quantity = min(item.quantity + quantity, product.stock)
        item.save()

    return JsonResponse({
        'success':    True,
        'message':    f'"{product.name}" added to cart!',
        'cart_count': cart.total_items,
    })


# ── Update quantity (AJAX POST) ───────────────────────────
@login_required
@require_POST
def cart_update(request):
    item_id = request.POST.get('item_id')
    action  = request.POST.get('action')   # 'increase' | 'decrease'

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if action == 'increase':
        if item.quantity < item.product.stock:
            item.quantity += 1
            item.save()
        else:
            return JsonResponse({
                'success': False,
                'message': 'Maximum stock reached.'
            })
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
            cart = get_cart(request.user)
            return JsonResponse({
                'success':    True,
                'quantity':   0,
                'subtotal':   '0',
                'total':      str(cart.total_price),
                'cart_count': cart.total_items,
            })

    cart = get_cart(request.user)
    return JsonResponse({
        'success':    True,
        'quantity':   item.quantity,
        'subtotal':   str(round(item.subtotal, 2)),
        'total':      str(round(cart.total_price, 2)),
        'cart_count': cart.total_items,
    })


# ── Remove item (AJAX POST) ───────────────────────────────
@login_required
@require_POST
def cart_remove(request):
    item_id = request.POST.get('item_id')
    item    = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()

    cart = get_cart(request.user)
    return JsonResponse({
        'success':    True,
        'total':      str(round(cart.total_price, 2)),
        'cart_count': cart.total_items,
    })


# ── Clear entire cart ─────────────────────────────────────
@login_required
@require_POST
def cart_clear(request):
    cart = get_cart(request.user)
    cart.items.all().delete()
    messages.info(request, 'Cart cleared.')
    return redirect('cart:detail')


# ── Wishlist toggle (AJAX POST) ───────────────────────────
@login_required
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    obj, created = Wishlist.objects.get_or_create(
        user=request.user, product=product
    )
    if not created:
        obj.delete()
        return JsonResponse({
            'success':    True,
            'in_wishlist': False,
            'message':    'Removed from wishlist.',
        })
    return JsonResponse({
        'success':    True,
        'in_wishlist': True,
        'message':    'Added to wishlist!',
    })


# ── Wishlist page ─────────────────────────────────────────
@login_required
def wishlist_page(request):
    wishlist = Wishlist.objects.filter(
        user=request.user
    ).select_related('product').prefetch_related(
        'product__images'
    ).order_by('-added_at')
    return render(request, 'cart/wishlist.html', {'wishlist': wishlist})