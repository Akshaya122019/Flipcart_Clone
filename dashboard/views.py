from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
import json
from users.forms import AdminUserCreateForm, AdminUserEditForm

from users.models import User
from products.models import Product, Category
from orders.models import Order, OrderItem
from payments.models import Payment
from products.forms import (
    CategoryForm, ProductForm,
    ProductImageForm, ProductVariantForm
)
from products.models import ProductImage, ProductVariant

# ══════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════

@staff_member_required
def admin_dashboard(request):
    today      = timezone.now().date()
    this_month = timezone.now().replace(day=1).date()
    last_30    = today - timedelta(days=30)

    # ── KPI cards ──
    total_revenue  = Payment.objects.filter(
                        status='success'
                     ).aggregate(t=Sum('amount'))['t'] or 0
    today_revenue  = Payment.objects.filter(
                        status='success',
                        created_at__date=today
                     ).aggregate(t=Sum('amount'))['t'] or 0
    month_revenue  = Payment.objects.filter(
                        status='success',
                        created_at__date__gte=this_month
                     ).aggregate(t=Sum('amount'))['t'] or 0

    total_orders   = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    today_orders   = Order.objects.filter(created_at__date=today).count()

    total_customers = User.objects.filter(role='buyer').count()
    new_customers   = User.objects.filter(
                        role='buyer',
                        date_joined__date__gte=last_30
                      ).count()

    total_sellers  = User.objects.filter(role='seller').count()
    total_products = Product.objects.filter(is_active=True).count()
    low_stock      = Product.objects.filter(
                        is_active=True, stock__lte=5
                     ).count()

    # ── Revenue chart (last 30 days) ──
    revenue_data = Payment.objects.filter(
        status='success',
        created_at__date__gte=last_30
    ).annotate(
        day=TruncDate('created_at')
    ).values('day').annotate(
        total=Sum('amount')
    ).order_by('day')

    chart_labels  = []
    chart_revenue = []
    date_map = {r['day']: float(r['total']) for r in revenue_data}
    for i in range(30):
        d = last_30 + timedelta(days=i)
        chart_labels.append(d.strftime('%d %b'))
        chart_revenue.append(date_map.get(d, 0))

    # ── Orders chart (last 30 days) ──
    orders_data = Order.objects.filter(
        created_at__date__gte=last_30
    ).annotate(
        day=TruncDate('created_at')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')

    order_map    = {o['day']: o['count'] for o in orders_data}
    chart_orders = [order_map.get(last_30 + timedelta(days=i), 0)
                    for i in range(30)]

    # ── Order status breakdown ──
    status_data = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    status_labels = [s['status'].title() for s in status_data]
    status_counts = [s['count'] for s in status_data]

    # ── Top products ──
    top_products = OrderItem.objects.values(
        'product__name', 'product__id'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum('subtotal')
    ).order_by('-total_sold')[:8]

    # ── Top categories ──
    top_categories = OrderItem.objects.values(
        'product__category__name'
    ).annotate(
        total=Sum('quantity')
    ).order_by('-total')[:6]

    # ── Recent orders ──
    recent_orders = Order.objects.select_related(
        'user', 'address'
    ).order_by('-created_at')[:10]

    # ── Recent users ──
    recent_users = User.objects.order_by('-date_joined')[:8]

    context = {
        # KPIs
        'total_revenue':   total_revenue,
        'today_revenue':   today_revenue,
        'month_revenue':   month_revenue,
        'total_orders':    total_orders,
        'pending_orders':  pending_orders,
        'today_orders':    today_orders,
        'total_customers': total_customers,
        'new_customers':   new_customers,
        'total_sellers':   total_sellers,
        'total_products':  total_products,
        'low_stock':       low_stock,
        # Charts
        'chart_labels':    json.dumps(chart_labels),
        'chart_revenue':   json.dumps(chart_revenue),
        'chart_orders':    json.dumps(chart_orders),
        'status_labels':   json.dumps(status_labels),
        'status_counts':   json.dumps(status_counts),
        # Tables
        'top_products':    top_products,
        'top_categories':  top_categories,
        'recent_orders':   recent_orders,
        'recent_users':    recent_users,
    }
    return render(request, 'dashboard/admin.html', context)


# ── Admin: All orders ─────────────────────────────────────
@staff_member_required
def admin_orders(request):
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    orders = Order.objects.select_related(
        'user', 'address'
    ).prefetch_related('items').order_by('-created_at')

    if status:
        orders = orders.filter(status=status)
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__email__icontains=search)  |
            Q(user__full_name__icontains=search)
        )

    context = {
        'orders':         orders,
        'status_filter':  status,
        'search':         search,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'dashboard/admin_orders.html', context)


# ── Admin: Update order status ────────────────────────────
@staff_member_required
def admin_order_update(request, pk):
    order = get_object_or_404(Order, id=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(
                request,
                f'Order {order.order_number} updated to {new_status}.'
            )
    return redirect('dashboard:admin_orders')


# ── Admin: All products ───────────────────────────────────
@staff_member_required
def admin_products(request):
    search   = request.GET.get('search', '')
    category = request.GET.get('category', '')

    products = Product.objects.select_related(
        'seller', 'category'
    ).prefetch_related('images').order_by('-created_at')

    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(brand__icontains=search)
        )
    if category:
        products = products.filter(category_id=category)

    categories = Category.objects.filter(is_active=True)
    context = {
        'products':   products,
        'categories': categories,
        'search':     search,
        'cat_filter': category,
    }
    return render(request, 'dashboard/admin_products.html', context)


# ── Admin: Toggle product active ─────────────────────────
@staff_member_required
def admin_product_toggle(request, pk):
    product = get_object_or_404(Product, id=pk)
    product.is_active = not product.is_active
    product.save()
    state = 'activated' if product.is_active else 'deactivated'
    messages.success(request, f'"{product.name}" {state}.')
    return redirect('dashboard:admin_products')


# ── Admin: All customers ──────────────────────────────────
@staff_member_required
def admin_customers(request):
    search = request.GET.get('search', '')
    role   = request.GET.get('role', '')

    users = User.objects.order_by('-date_joined')
    if search:
        users = users.filter(
            Q(email__icontains=search)     |
            Q(full_name__icontains=search) |
            Q(username__icontains=search)
        )
    if role:
        users = users.filter(role=role)

    context = {
        'users':  users,
        'search': search,
        'role':   role,
    }
    return render(request, 'dashboard/admin_customers.html', context)


# ── Admin: Toggle user active ─────────────────────────────
@staff_member_required
def admin_user_toggle(request, pk):
    user = get_object_or_404(User, id=pk)
    if user != request.user:
        user.is_active = not user.is_active
        user.save()
        state = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'{user.email} {state}.')
    return redirect('dashboard:admin_customers')


# ══════════════════════════════════════════════════════════
#  SELLER DASHBOARD
# ══════════════════════════════════════════════════════════

def seller_required(view_func):
    """Decorator: allow only sellers."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ('seller', 'admin'):
            messages.error(request, 'Seller access required.')
            return redirect('products:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@seller_required
def seller_dashboard(request):
    seller    = request.user
    today     = timezone.now().date()
    last_30   = today - timedelta(days=30)

    # ── KPIs ──
    my_products    = Product.objects.filter(seller=seller)
    my_product_ids = my_products.values_list('id', flat=True)

    my_order_items = OrderItem.objects.filter(
        product_id__in=my_product_ids
    ).select_related('order', 'product')

    total_revenue = my_order_items.filter(
        order__status__in=['confirmed','processing','shipped','delivered']
    ).aggregate(t=Sum('subtotal'))['t'] or 0

    month_revenue = my_order_items.filter(
        order__status__in=['confirmed','processing','shipped','delivered'],
        order__created_at__date__gte=today.replace(day=1)
    ).aggregate(t=Sum('subtotal'))['t'] or 0

    total_orders  = my_order_items.values(
        'order'
    ).distinct().count()

    pending_dispatch = my_order_items.filter(
        order__status='confirmed'
    ).values('order').distinct().count()

    total_products  = my_products.filter(is_active=True).count()
    low_stock_items = my_products.filter(is_active=True, stock__lte=5)

    # ── Revenue chart ──
    revenue_data = my_order_items.filter(
        order__created_at__date__gte=last_30,
        order__status__in=['confirmed','processing','shipped','delivered']
    ).annotate(
        day=TruncDate('order__created_at')
    ).values('day').annotate(
        total=Sum('subtotal')
    ).order_by('day')

    chart_labels  = []
    chart_revenue = []
    date_map = {r['day']: float(r['total']) for r in revenue_data}
    for i in range(30):
        d = last_30 + timedelta(days=i)
        chart_labels.append(d.strftime('%d %b'))
        chart_revenue.append(date_map.get(d, 0))

    # ── Top selling products ──
    top_products = my_order_items.values(
        'product__name', 'product__id'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum('subtotal')
    ).order_by('-total_sold')[:5]

    # ── Recent orders for this seller ──
    recent_order_items = my_order_items.select_related(
        'order__user', 'order__address', 'product'
    ).order_by('-order__created_at')[:10]

    context = {
        'total_revenue':     total_revenue,
        'month_revenue':     month_revenue,
        'total_orders':      total_orders,
        'pending_dispatch':  pending_dispatch,
        'total_products':    total_products,
        'low_stock_items':   low_stock_items,
        'chart_labels':      json.dumps(chart_labels),
        'chart_revenue':     json.dumps(chart_revenue),
        'top_products':      top_products,
        'recent_order_items':recent_order_items,
    }
    return render(request, 'dashboard/seller.html', context)


# ── Seller: My products ───────────────────────────────────
@seller_required
def seller_products(request):
    search   = request.GET.get('search', '')
    products = Product.objects.filter(
        seller=request.user
    ).prefetch_related('images').order_by('-created_at')

    if search:
        products = products.filter(name__icontains=search)

    return render(request, 'dashboard/seller_products.html', {
        'products': products,
        'search':   search,
    })


# ── Seller: Toggle product ────────────────────────────────
@seller_required
def seller_product_toggle(request, pk):
    product = get_object_or_404(Product, id=pk, seller=request.user)
    product.is_active = not product.is_active
    product.save()
    messages.success(
        request,
        f'"{product.name}" {"activated" if product.is_active else "deactivated"}.'
    )
    return redirect('dashboard:seller_products')


# ── Seller: Orders ────────────────────────────────────────
@seller_required
def seller_orders(request):
    seller         = request.user
    my_product_ids = Product.objects.filter(
        seller=seller
    ).values_list('id', flat=True)

    status = request.GET.get('status', '')
    items  = OrderItem.objects.filter(
        product_id__in=my_product_ids
    ).select_related(
        'order', 'order__user', 'order__address', 'product'
    ).order_by('-order__created_at')

    if status:
        items = items.filter(order__status=status)

    context = {
        'order_items':    items,
        'status_filter':  status,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'dashboard/seller_orders.html', context)


# ── Seller: Mark dispatched ───────────────────────────────
@seller_required
def seller_dispatch(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Verify seller owns at least one item in this order
    my_product_ids = Product.objects.filter(
        seller=request.user
    ).values_list('id', flat=True)

    has_item = order.items.filter(
        product_id__in=my_product_ids
    ).exists()

    if has_item and order.status == 'confirmed':
        order.status = 'shipped'
        order.save()
        messages.success(
            request,
            f'Order {order.order_number} marked as shipped.'
        )
    else:
        messages.error(request, 'Cannot update this order.')
    return redirect('dashboard:seller_orders')


# ── Seller: Profile ───────────────────────────────────────
@seller_required
def seller_profile(request):
    from users.forms import ProfileUpdateForm
    form = ProfileUpdateForm(
        request.POST  or None,
        request.FILES or None,
        instance=request.user
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('dashboard:seller_profile')
    return render(request, 'dashboard/seller_profile.html', {'form': form})

@staff_member_required
def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'dashboard/category_list.html', {
        'categories': categories
    })


@staff_member_required
def category_add(request):
    form = CategoryForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category created successfully.')
        return redirect('dashboard:category_list')
    return render(request, 'dashboard/category_form.html', {
        'form':  form,
        'title': 'Add Category',
    })


@staff_member_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(
        request.POST  or None,
        request.FILES or None,
        instance=category
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('dashboard:category_list')
    return render(request, 'dashboard/category_form.html', {
        'form':     form,
        'title':    'Edit Category',
        'category': category,
    })


@staff_member_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('dashboard:category_list')
    return render(request, 'dashboard/confirm_delete.html', {
        'object': category,
        'title':  'Delete Category',
        'back':   'dashboard:category_list',
    })


# ══════════════════════════════════════════════════════════
#  PRODUCT CRUD (Admin)
# ══════════════════════════════════════════════════════════

@staff_member_required
def product_add(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        # Admin adds on behalf of seller — assign to self or first seller
        if request.user.role == 'admin':
            seller = User.objects.filter(
                role='seller'
            ).first() or request.user
            product.seller = seller
        else:
            product.seller = request.user
        product.save()
        messages.success(
            request,
            f'Product "{product.name}" created. Now add images below.'
        )
        return redirect('dashboard:product_edit', pk=product.pk)
    return render(request, 'dashboard/product_form.html', {
        'form':  form,
        'title': 'Add New Product',
    })


@staff_member_required
def product_edit(request, pk):
    product  = get_object_or_404(Product, pk=pk)
    form     = ProductForm(
        request.POST  or None,
        instance=product
    )
    img_form     = ProductImageForm()
    variant_form = ProductVariantForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Save main product info ──
        if action == 'save_product':
            if form.is_valid():
                form.save()
                messages.success(request, 'Product updated.')
                return redirect('dashboard:product_edit', pk=pk)

        # ── Add image ──
        elif action == 'add_image':
            print("=" * 50)
            print("ACTION: add_image triggered")
            print("FILES:", request.FILES)
            print("POST:", request.POST)
            img_form = ProductImageForm(request.POST, request.FILES)
            print("Form valid:", img_form.is_valid())
            print("Form errors:", img_form.errors)
            print("=" * 50)
            if img_form.is_valid():
                img = img_form.save(commit=False)
                img.product = product
                if img.is_primary:
                    ProductImage.objects.filter(
                        product=product
                    ).update(is_primary=False)
                img.save()
                print("SAVED IMAGE:", img.image.path)
                messages.success(request, 'Image added.')
                return redirect('dashboard:product_edit', pk=pk)
            else:
                messages.error(request, f'Image upload failed: {img_form.errors}')

        # ── Delete image ──
        elif action == 'delete_image':
            img_id = request.POST.get('image_id')
            ProductImage.objects.filter(
                id=img_id, product=product
            ).delete()
            messages.success(request, 'Image deleted.')
            return redirect('dashboard:product_edit', pk=pk)

        # ── Add variant ──
        elif action == 'add_variant':
            variant_form = ProductVariantForm(request.POST)
            if variant_form.is_valid():
                v = variant_form.save(commit=False)
                v.product = product
                v.save()
                messages.success(request, 'Variant added.')
                return redirect('dashboard:product_edit', pk=pk)

        # ── Delete variant ──
        elif action == 'delete_variant':
            var_id = request.POST.get('variant_id')
            ProductVariant.objects.filter(
                id=var_id, product=product
            ).delete()
            messages.success(request, 'Variant deleted.')
            return redirect('dashboard:product_edit', pk=pk)

    images   = product.images.all()
    variants = product.variants.all()

    return render(request, 'dashboard/product_edit.html', {
        'form':         form,
        'product':      product,
        'img_form':     img_form,
        'variant_form': variant_form,
        'images':       images,
        'variants':     variants,
    })


@staff_member_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, f'"{product.name}" deleted.')
        return redirect('dashboard:admin_products')
    return render(request, 'dashboard/confirm_delete.html', {
        'object': product,
        'title':  'Delete Product',
        'back':   'dashboard:admin_products',
    })


# ══════════════════════════════════════════════════════════
#  SELLER: Add/Edit own products
# ══════════════════════════════════════════════════════════

@seller_required
def seller_product_add(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.save()
        messages.success(
            request,
            f'"{product.name}" created. Now add images.'
        )
        return redirect('dashboard:seller_product_edit', pk=product.pk)
    return render(request, 'dashboard/product_form.html', {
        'form':      form,
        'title':     'Add New Product',
        'is_seller': True,
    })


@seller_required
def seller_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    form         = ProductForm(request.POST or None, instance=product)
    img_form     = ProductImageForm()
    variant_form = ProductVariantForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_product' and form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('dashboard:seller_product_edit', pk=pk)

        elif action == 'add_image':
            img_form = ProductImageForm(request.POST, request.FILES)
            if img_form.is_valid():
                img = img_form.save(commit=False)
                img.product = product
                if img.is_primary:
                    ProductImage.objects.filter(
                        product=product
                    ).update(is_primary=False)
                img.save()
                messages.success(request, 'Image added.')
                return redirect('dashboard:seller_product_edit', pk=pk)

        elif action == 'delete_image':
            img_id = request.POST.get('image_id')
            ProductImage.objects.filter(
                id=img_id, product=product
            ).delete()
            return redirect('dashboard:seller_product_edit', pk=pk)

        elif action == 'add_variant':
            variant_form = ProductVariantForm(request.POST)
            if variant_form.is_valid():
                v = variant_form.save(commit=False)
                v.product = product
                v.save()
                messages.success(request, 'Variant added.')
                return redirect('dashboard:seller_product_edit', pk=pk)

        elif action == 'delete_variant':
            var_id = request.POST.get('variant_id')
            ProductVariant.objects.filter(
                id=var_id, product=product
            ).delete()
            return redirect('dashboard:seller_product_edit', pk=pk)

    return render(request, 'dashboard/product_edit.html', {
        'form':         form,
        'product':      product,
        'img_form':     img_form,
        'variant_form': variant_form,
        'images':       product.images.all(),
        'variants':     product.variants.all(),
        'is_seller':    True,
    })



# ══════════════════════════════════════════════════════════
#  USER MANAGEMENT (Admin only)
# ══════════════════════════════════════════════════════════
@staff_member_required
def user_create(request):
    """Admin creates a seller or admin account."""
    form = AdminUserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(
            request,
            f'{user.get_role_display()} account created for {user.email}.'
        )
        return redirect('dashboard:admin_customers')
    return render(request, 'dashboard/user_form.html', {
        'form':  form,
        'title': 'Add Seller / Admin',
    })


@staff_member_required
def user_edit(request, pk):
    """Admin edits any user's details and role."""
    user = get_object_or_404(User, pk=pk)
    # Prevent editing yourself via this form
    if user == request.user:
        messages.warning(
            request,
            'Edit your own profile via the profile page.'
        )
        return redirect('dashboard:admin_customers')

    form = AdminUserEditForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{user.email} updated.')
        return redirect('dashboard:admin_customers')
    return render(request, 'dashboard/user_form.html', {
        'form':  form,
        'title': f'Edit User — {user.email}',
        'edit_user': user,
    })


@staff_member_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('dashboard:admin_customers')
    if request.method == 'POST':
        email = user.email
        user.delete()
        messages.success(request, f'{email} deleted.')
        return redirect('dashboard:admin_customers')
    return render(request, 'dashboard/confirm_delete.html', {
        'object': user,
        'title':  'Delete User',
        'back':   'dashboard:admin_customers',
    })