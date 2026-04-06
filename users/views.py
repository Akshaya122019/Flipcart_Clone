from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import RegisterForm, LoginForm, ProfileUpdateForm, CustomPasswordChangeForm
from .models import User
from cart.models import Wishlist


# ── Register ──────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome, {user.full_name or user.username}! Account created.')
        return redirect('products:home')

    return render(request, 'users/register.html', {'form': form})


# ── Login ─────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.full_name or user.username}!')
        next_url = request.GET.get('next', 'products:home')
        return redirect(next_url)

    return render(request, 'users/login.html', {'form': form})


# ── Logout ────────────────────────────────────────────────
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('products:home')


# ── Profile ───────────────────────────────────────────────
@login_required
def profile_view(request):
    from orders.models import Order
    orders   = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    wishlist = Wishlist.objects.filter(user=request.user).select_related('product')[:6]
    return render(request, 'users/profile.html', {
        'orders':   orders,
        'wishlist': wishlist,
    })


# ── Profile edit ──────────────────────────────────────────
@login_required
def profile_edit_view(request):
    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('users:profile')

    return render(request, 'users/profile_edit.html', {'form': form})


# ── Password change ───────────────────────────────────────
@login_required
def password_change_view(request):
    form = CustomPasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully.')
        return redirect('users:profile')

    return render(request, 'users/password_change.html', {'form': form})


# ── Wishlist page ─────────────────────────────────────────
@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.filter(
        user=request.user
    ).select_related('product').order_by('-added_at')
    return render(request, 'users/wishlist.html', {'wishlist': wishlist})