from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/<int:order_id>/',     views.razorpay_pay,    name='razorpay_pay'),
    path('verify/',                 views.razorpay_verify, name='razorpay_verify'),
    path('failed/<int:order_id>/',  views.payment_failed,  name='failed'),
    path('webhook/',                views.razorpay_webhook,name='webhook'),
    path('retry/<int:order_id>/',   views.retry_payment,   name='retry'),
    path('history/',                views.payment_history, name='history'),
]