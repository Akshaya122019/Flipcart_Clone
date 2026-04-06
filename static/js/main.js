$(document).ready(function () {

  // ── CSRF helper for all AJAX POST requests ──
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      document.cookie.split(';').forEach(function (cookie) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        }
      });
    }
    return cookieValue;
  }

  $.ajaxSetup({
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  });

  // ── Add to cart (AJAX) ──
  $(document).on('click', '.btn-add-cart', function (e) {
    e.preventDefault();
    const btn     = $(this);
    const url     = btn.data('url');
    const product = btn.data('product');

    btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span>');

    $.post(url, { product_id: product }, function (res) {
      if (res.success) {
        // Update badge
        $('#cart-badge').text(res.cart_count).show();
        // Visual feedback
        btn.html('<i class="bi bi-check-lg me-1"></i> Added').addClass('btn-success');
        setTimeout(() => {
          btn.html('<i class="bi bi-cart-plus me-1"></i> Add to Cart')
             .removeClass('btn-success').prop('disabled', false);
        }, 1800);
        showToast(res.message || 'Added to cart!', 'success');
      } else {
        btn.prop('disabled', false).html('<i class="bi bi-cart-plus me-1"></i> Add to Cart');
        showToast(res.message || 'Something went wrong.', 'danger');
      }
    }).fail(function () {
      btn.prop('disabled', false).html('<i class="bi bi-cart-plus me-1"></i> Add to Cart');
      showToast('Please login to add items to cart.', 'warning');
    });
  });

  // ── Wishlist toggle (AJAX) ──
  $(document).on('click', '.btn-wishlist', function (e) {
    e.preventDefault();
    const btn = $(this);
    const url = btn.data('url');

    $.post(url, {}, function (res) {
      if (res.success) {
        if (res.in_wishlist) {
          btn.html('<i class="bi bi-heart-fill text-danger"></i>');
        } else {
          btn.html('<i class="bi bi-heart"></i>');
        }
        showToast(res.message, 'success');
      }
    });
  });

  // ── Cart quantity update (AJAX) ──
  $(document).on('click', '.btn-qty', function () {
    const btn      = $(this);
    const action   = btn.data('action');   // 'increase' or 'decrease'
    const itemId   = btn.data('item');
    const url      = btn.data('url');

    $.post(url, { action: action, item_id: itemId }, function (res) {
      if (res.success) {
        $(`#qty-${itemId}`).text(res.quantity);
        $(`#subtotal-${itemId}`).text('₹' + res.subtotal);
        $('#cart-total').text('₹' + res.total);
        $('#cart-badge').text(res.cart_count);
        if (res.quantity === 0) {
          $(`#cart-row-${itemId}`).fadeOut(300, function () { $(this).remove(); });
        }
      }
    });
  });

  // ── Remove from cart (AJAX) ──
  $(document).on('click', '.btn-remove-cart', function (e) {
    e.preventDefault();
    const btn    = $(this);
    const itemId = btn.data('item');
    const url    = btn.data('url');

    if (!confirm('Remove this item from cart?')) return;

    $.post(url, { item_id: itemId }, function (res) {
      if (res.success) {
        $(`#cart-row-${itemId}`).fadeOut(300, function () { $(this).remove(); });
        $('#cart-total').text('₹' + res.total);
        $('#cart-badge').text(res.cart_count);
        showToast('Item removed from cart.', 'info');
        if (res.cart_count === 0) location.reload();
      }
    });
  });

  // ── Toast notification ──
  window.showToast = function (message, type = 'success') {
    const id   = 'toast-' + Date.now();
    const icon = {
      success: 'bi-check-circle-fill',
      danger:  'bi-x-circle-fill',
      warning: 'bi-exclamation-triangle-fill',
      info:    'bi-info-circle-fill',
    }[type] || 'bi-info-circle-fill';

    const html = `
      <div id="${id}" class="toast align-items-center text-bg-${type} border-0 mb-2"
           role="alert" style="min-width:260px">
        <div class="d-flex">
          <div class="toast-body">
            <i class="bi ${icon} me-2"></i>${message}
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto"
                  data-bs-dismiss="toast"></button>
        </div>
      </div>`;

    if (!$('#toast-container').length) {
      $('body').append('<div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index:9999"></div>');
    }
    $('#toast-container').append(html);
    const toastEl = document.getElementById(id);
    new bootstrap.Toast(toastEl, { delay: 3500 }).show();
    $(toastEl).on('hidden.bs.toast', function () { $(this).remove(); });
  };

  // ── Image gallery (product detail) ──
  $(document).on('click', '.thumb-img', function () {
    const src = $(this).data('full');
    $('#main-product-img').attr('src', src);
    $('.thumb-img').removeClass('active');
    $(this).addClass('active');
  });

  // ── Pincode check (product detail) ──
  $('#btn-check-pin').on('click', function () {
    const pin = $('#pincode-input').val().trim();
    if (pin.length !== 6 || isNaN(pin)) {
      showToast('Enter a valid 6-digit pincode.', 'warning');
      return;
    }
    $('#pin-result').html(
      `<span class="text-success"><i class="bi bi-check-circle me-1"></i>
       Delivery available for <strong>${pin}</strong> by Tomorrow</span>`
    );
  });

});