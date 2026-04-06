from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('',                           views.cart_detail,    name='detail'),
    path('add/',                       views.cart_add,       name='add'),
    path('update/',                    views.cart_update,    name='update'),
    path('remove/',                    views.cart_remove,    name='remove'),
    path('clear/',                     views.cart_clear,     name='clear'),
    path('wishlist/<int:product_id>/', views.wishlist_toggle,name='wishlist_toggle'),
    path('wishlist/',                  views.wishlist_page,  name='wishlist'),
]