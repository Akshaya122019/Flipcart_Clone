from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('',                              views.home,           name='home'),
    path('search/',                       views.search_view,    name='search'),
    path('category/<slug:slug>/',         views.category_view,  name='category'),
    path('product/<slug:slug>/',          views.product_detail, name='detail'),
    path('review/<int:product_id>/',      views.submit_review,  name='review'),
]