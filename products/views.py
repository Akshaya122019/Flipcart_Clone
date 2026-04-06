from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Product, Category, Review
from cart.models import Wishlist


# ── Home ──────────────────────────────────────────────────
def home(request):
    featured   = Product.objects.filter(
                    is_active=True, is_featured=True
                 ).prefetch_related('images')[:8]
    new_arrivals = Product.objects.filter(
                    is_active=True
                 ).prefetch_related('images').order_by('-created_at')[:8]
    categories = Category.objects.filter(
                    is_active=True, parent=None
                 ).prefetch_related('children')[:8]
    deals      = Product.objects.filter(
                    is_active=True, discount__gte=20
                 ).prefetch_related('images').order_by('-discount')[:8]

    context = {
        'featured':     featured,
        'new_arrivals': new_arrivals,
        'categories':   categories,
        'deals':        deals,
    }
    return render(request, 'products/home.html', context)


# ── Category ──────────────────────────────────────────────
def category_view(request, slug):
    category     = get_object_or_404(Category, slug=slug, is_active=True)
    subcategories = category.children.filter(is_active=True)

    products = Product.objects.filter(
        is_active=True, category=category
    ).prefetch_related('images')

    # ── Filters ──
    brand     = request.GET.getlist('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    rating    = request.GET.get('rating')
    sort      = request.GET.get('sort', 'popular')

    if brand:
        products = products.filter(brand__in=brand)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # ── Sorting ──
    sort_map = {
        'popular':   '-created_at',
        'price_asc': 'price',
        'price_desc':'-price',
        'newest':    '-created_at',
        'discount':  '-discount',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    # ── Brands for filter sidebar ──
    brands = Product.objects.filter(
        is_active=True, category=category
    ).exclude(brand='').values_list('brand', flat=True).distinct()

    # ── Pagination ──
    paginator   = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    context = {
        'category':      category,
        'subcategories': subcategories,
        'page_obj':      page_obj,
        'brands':        brands,
        'sort':          sort,
        'total':         paginator.count,
    }
    return render(request, 'products/category.html', context)


# ── Product detail ────────────────────────────────────────
def product_detail(request, slug):
    product  = get_object_or_404(Product, slug=slug, is_active=True)
    images   = product.images.all()
    variants = product.variants.all()
    reviews  = product.reviews.select_related('user').order_by('-created_at')
    related  = Product.objects.filter(
                    category=product.category, is_active=True
               ).exclude(id=product.id).prefetch_related('images')[:6]

    # Check wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user, product=product
        ).exists()

    # Rating breakdown
    rating_data = reviews.aggregate(avg=Avg('rating'), count=Count('id'))
    rating_breakdown = {}
    for i in range(5, 0, -1):
        cnt = reviews.filter(rating=i).count()
        rating_breakdown[i] = {
            'count': cnt,
            'pct':   round((cnt / rating_data['count'] * 100)
                           if rating_data['count'] else 0),
        }

    # Review form
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(
            user=request.user, product=product
        ).first()

    context = {
        'product':          product,
        'images':           images,
        'variants':         variants,
        'reviews':          reviews,
        'related':          related,
        'in_wishlist':      in_wishlist,
        'rating_data':      rating_data,
        'rating_breakdown': rating_breakdown,
        'user_review':      user_review,
    }
    return render(request, 'products/detail.html', context)


# ── Search ────────────────────────────────────────────────
def search_view(request):
    query    = request.GET.get('q', '').strip()
    products = Product.objects.none()
    total    = 0

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query)        |
            Q(description__icontains=query) |
            Q(brand__icontains=query)       |
            Q(category__name__icontains=query),
            is_active=True
        ).prefetch_related('images').distinct()
        total = products.count()

    # Sort
    sort    = request.GET.get('sort', 'popular')
    sort_map = {
        'popular':    '-created_at',
        'price_asc':  'price',
        'price_desc': '-price',
        'discount':   '-discount',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    paginator   = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    context = {
        'query':    query,
        'page_obj': page_obj,
        'total':    total,
        'sort':     sort,
    }
    return render(request, 'products/search.html', context)


# ── Submit review (AJAX) ──────────────────────────────────
def submit_review(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Login required'})

    if request.method != 'POST':
        return JsonResponse({'success': False})

    product = get_object_or_404(Product, id=product_id)
    rating  = request.POST.get('rating')
    title   = request.POST.get('title', '')
    body    = request.POST.get('body', '')

    if not rating or not body:
        return JsonResponse({'success': False, 'message': 'Rating and review required'})

    review, created = Review.objects.update_or_create(
        user=request.user, product=product,
        defaults={'rating': rating, 'title': title, 'body': body}
    )
    return JsonResponse({
        'success':  True,
        'message':  'Review submitted!',
        'created':  created,
        'username': request.user.username,
        'rating':   review.rating,
        'title':    review.title,
        'body':     review.body,
    })