from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [

    # ── Admin overview ──
    path('admin/',
         views.admin_dashboard,       name='admin'),
    path('admin/orders/',
         views.admin_orders,          name='admin_orders'),
    path('admin/orders/<int:pk>/update/',
         views.admin_order_update,    name='admin_order_update'),
    path('admin/products/',
         views.admin_products,        name='admin_products'),
    path('admin/products/add/',
         views.product_add,           name='product_add'),
    path('admin/products/<int:pk>/edit/',
         views.product_edit,          name='product_edit'),
    path('admin/products/<int:pk>/delete/',
         views.product_delete,        name='product_delete'),
    path('admin/products/<int:pk>/toggle/',
         views.admin_product_toggle,  name='admin_product_toggle'),
    path('admin/customers/',
         views.admin_customers,       name='admin_customers'),
    path('admin/customers/<int:pk>/toggle/',
         views.admin_user_toggle,     name='admin_user_toggle'),

    # ── Categories ──
    path('admin/categories/',
         views.category_list,         name='category_list'),
    path('admin/categories/add/',
         views.category_add,          name='category_add'),
    path('admin/categories/<int:pk>/edit/',
         views.category_edit,         name='category_edit'),
    path('admin/categories/<int:pk>/delete/',
         views.category_delete,       name='category_delete'),

    # ── Seller ──
    path('seller/',
         views.seller_dashboard,      name='seller_dashboard'),
    path('seller/products/',
         views.seller_products,       name='seller_products'),
    path('seller/products/add/',
         views.seller_product_add,    name='seller_product_add'),
    path('seller/products/<int:pk>/edit/',
         views.seller_product_edit,   name='seller_product_edit'),
    path('seller/products/<int:pk>/toggle/',
         views.seller_product_toggle, name='seller_product_toggle'),
    path('seller/orders/',
         views.seller_orders,         name='seller_orders'),
    path('seller/orders/<int:order_id>/dispatch/',
         views.seller_dispatch,       name='seller_dispatch'),
    path('seller/profile/',
         views.seller_profile,        name='seller_profile'),
     path('admin/users/add/',
     views.user_create,   name='user_create'),
path('admin/users/<int:pk>/edit/',
     views.user_edit,     name='user_edit'),
path('admin/users/<int:pk>/delete/',
     views.user_delete,   name='user_delete'),
]

