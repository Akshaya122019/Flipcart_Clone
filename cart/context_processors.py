def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            from cart.models import Cart
            cart  = Cart.objects.get(user=request.user)
            count = cart.total_items
        except Exception:
            count = 0
    return {'cart_count': count}