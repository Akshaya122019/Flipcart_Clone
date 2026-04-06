import razorpay
import hmac
import hashlib
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib import messages

from orders.models import Order
from .models import Payment


# ── Razorpay client ───────────────────────────────────────
def get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


# ── Initiate payment ──────────────────────────────────────
@login_required
def razorpay_pay(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Prevent re-payment if already paid
    try:
        if order.payment.status == 'success':
            messages.info(request, 'This order is already paid.')
            return redirect('orders:detail', pk=order.id)
    except Payment.DoesNotExist:
        pass

    client = get_razorpay_client()

    # Amount in paise (Razorpay uses smallest currency unit)
    amount_paise = int(order.grand_total * 100)

    # Create Razorpay order
    razorpay_order = client.order.create({
        'amount':   amount_paise,
        'currency': 'INR',
        'receipt':  order.order_number,
        'notes': {
            'order_id':   str(order.id),
            'user_email': request.user.email,
        }
    })

    # Save or update Payment record
    payment, _ = Payment.objects.update_or_create(
        order=order,
        defaults={
            'user':              request.user,
            'amount':            order.grand_total,
            'razorpay_order_id': razorpay_order['id'],
            'status':            'created',
        }
    )

    context = {
        'order':            order,
        'payment':          payment,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key':     settings.RAZORPAY_KEY_ID,
        'amount_paise':     amount_paise,
        'user_name':        request.user.full_name or request.user.username,
        'user_email':       request.user.email,
        'user_phone':       request.user.phone or '',
    }
    return render(request, 'payments/razorpay_pay.html', context)


# ── Verify payment (AJAX callback from Razorpay) ──────────
@csrf_exempt
@require_POST
def razorpay_verify(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    razorpay_order_id   = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature  = data.get('razorpay_signature')

    # Find payment record
    try:
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Payment not found'}, status=404)

    # ── Verify signature ──
    key_secret = settings.RAZORPAY_KEY_SECRET.encode()
    message    = f'{razorpay_order_id}|{razorpay_payment_id}'.encode()
    generated  = hmac.new(key_secret, message, hashlib.sha256).hexdigest()

    if generated == razorpay_signature:
        # Payment verified
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature  = razorpay_signature
        payment.status              = 'success'
        payment.save()

        # Update order
        order        = payment.order
        order.status = 'confirmed'
        order.save()

        return JsonResponse({
            'success':    True,
            'order_id':   order.id,
            'redirect':   f'/orders/success/{order.id}/',
        })
    else:
        # Signature mismatch
        payment.status = 'failed'
        payment.save()
        payment.order.status = 'pending'
        payment.order.save()

        return JsonResponse({
            'success': False,
            'message': 'Payment verification failed. Please contact support.'
        }, status=400)


# ── Payment failed page ───────────────────────────────────
@login_required
def payment_failed(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    try:
        payment = order.payment
    except Payment.DoesNotExist:
        payment = None
    return render(request, 'payments/failed.html', {
        'order':   order,
        'payment': payment,
    })


# ── Razorpay webhook (server-to-server) ───────────────────
@csrf_exempt
@require_POST
def razorpay_webhook(request):
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)

    if webhook_secret:
        signature  = request.headers.get('X-Razorpay-Signature', '')
        body       = request.body
        key_secret = webhook_secret.encode()
        generated  = hmac.new(key_secret, body, hashlib.sha256).hexdigest()

        if generated != signature:
            return HttpResponse('Invalid signature', status=400)

    try:
        payload = json.loads(request.body)
        event   = payload.get('event')

        if event == 'payment.captured':
            payment_entity  = payload['payload']['payment']['entity']
            razorpay_pay_id = payment_entity['id']
            razorpay_ord_id = payment_entity['order_id']

            try:
                payment = Payment.objects.get(
                    razorpay_order_id=razorpay_ord_id
                )
                if payment.status != 'success':
                    payment.razorpay_payment_id = razorpay_pay_id
                    payment.status              = 'success'
                    payment.save()
                    payment.order.status = 'confirmed'
                    payment.order.save()
            except Payment.DoesNotExist:
                pass

        elif event == 'payment.failed':
            payment_entity  = payload['payload']['payment']['entity']
            razorpay_ord_id = payment_entity['order_id']
            try:
                payment        = Payment.objects.get(
                    razorpay_order_id=razorpay_ord_id
                )
                payment.status = 'failed'
                payment.save()
            except Payment.DoesNotExist:
                pass

    except Exception as e:
        return HttpResponse(f'Webhook error: {e}', status=400)

    return HttpResponse('OK', status=200)


# ── Retry payment ─────────────────────────────────────────
@login_required
def retry_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return redirect('payments:razorpay_pay', order_id=order.id)


# ── Payment history ───────────────────────────────────────
@login_required
def payment_history(request):
    payments = Payment.objects.filter(
        user=request.user
    ).select_related('order').order_by('-created_at')
    return render(request, 'payments/history.html', {'payments': payments})