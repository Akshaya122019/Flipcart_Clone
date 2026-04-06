from .models import Category

def categories(request):
    try:
        cats = Category.objects.filter(
            is_active=True, parent=None
        ).prefetch_related('children')[:12]
    except Exception:
        cats = []
    return {'nav_categories': cats}