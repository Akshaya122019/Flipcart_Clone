from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('',                      views.order_list,        name='list'),
    path('<int:pk>/',             views.order_detail,      name='detail'),
    path('<int:pk>/cancel/',      views.order_cancel,      name='cancel'),
    path('checkout/',             views.checkout,          name='checkout'),
    path('checkout/summary/',     views.checkout_summary,  name='checkout_summary'),
    path('success/<int:pk>/',     views.order_success,     name='success'),
]