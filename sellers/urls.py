from django.urls import path
from django.shortcuts import render

app_name = 'sellers'

def placeholder(request):
    return render(request, 'base.html')

urlpatterns = [
    path('register/', placeholder, name='register'),
    path('dashboard/', placeholder, name='dashboard'),
]