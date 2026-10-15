/**
 * NezaMateriales — Módulo de Carrito de Compras & Proceso de Pago
 */

import { createQuoteAPI } from './api.js';
import { showToast } from './app.js';

const CART_KEY = 'neza_materiales_cart';

export function getCart() {
  const saved = localStorage.getItem(CART_KEY);
  return saved ? JSON.parse(saved) : [];
}

export function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartBadge();
}

export function addToCart(product, quantity = 1) {
  let cart = getCart();
  const existing = cart.find(item => item.id === product.id);

  if (existing) {
    existing.quantity = parseFloat((existing.quantity + quantity).toFixed(4));
  } else {
    cart.push({
      id: product.id,
      name: product.name,
      price: parseFloat(product.price),
      unit: product.unit,
      quantity: parseFloat(quantity)
    });
  }

  saveCart(cart);
  renderCartView();
}

export function removeFromCart(id) {
  let cart = getCart().filter(item => item.id !== id);
  saveCart(cart);
  renderCartView();
}

export function updateCartQuantity(id, newQty) {
  let cart = getCart();
  const item = cart.find(i => i.id === id);
  if (item) {
    if (newQty <= 0) {
      removeFromCart(id);
      return;
    }
    item.quantity = parseFloat(newQty);
    saveCart(cart);
    renderCartView();
  }
}

export function clearCart() {
  localStorage.removeItem(CART_KEY);
  updateCartBadge();
  renderCartView();
}

export function updateCartBadge() {
  const badge = document.getElementById('cart-count-badge');
  if (!badge) return;
  const cart = getCart();
  const totalCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  badge.innerText = Math.round(totalCount);
}

export function initCartView() {
  updateCartBadge();
  renderCartView();

  const checkoutForm = document.getElementById('checkout-form');
  const deliveryRadios = document.querySelectorAll('input[name="delivery_method"]');
  const addressGroup = document.getElementById('address-form-group');

  if (deliveryRadios) {
    deliveryRadios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        if (addressGroup) {
          addressGroup.style.display = e.target.value === 'flete_neza' ? 'block' : 'none';
        }
      });
    });
  }

  if (checkoutForm) {
    checkoutForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const cart = getCart();
      if (cart.length === 0) {
        showToast('⚠️ Tu carrito está vacío', 'error');
        return;
      }

      const clientName = document.getElementById('client-name').value.trim();
      const clientPhone = document.getElementById('client-phone').value.trim();
      const deliveryMethod = document.querySelector('input[name="delivery_method"]:checked').value;
      const deliveryAddress = document.getElementById('delivery-address') ? document.getElementById('delivery-address').value.trim() : '';

      const quotePayload = {
        client_name: clientName,
        client_phone: clientPhone,
        delivery_method: deliveryMethod,
        delivery_address: deliveryAddress,
        items: cart.map(item => ({
          product_id: item.id,
          quantity: item.quantity,
          unit_price: item.price
        }))
      };

      try {
        const orderResult = await createQuoteAPI(quotePayload);
        showOrderConfirmationModal(orderResult, deliveryMethod);
        clearCart();
      } catch (err) {
        showToast(`❌ Error al procesar pedido: ${err.message}`, 'error');
      }
    });
  }
}

export function renderCartView() {
  const container = document.getElementById('cart-items-container');
  const totalAmountEl = document.getElementById('cart-total-amount');
  const shippingCostEl = document.getElementById('cart-shipping-cost');
  const grandTotalEl = document.getElementById('cart-grand-total');
  
  if (!container) return;

  const cart = getCart();
  if (cart.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
        <p style="font-size: 3rem; margin-bottom: 0.5rem;">🛒</p>
        <p style="font-size: 1.1rem; font-weight: 600;">Tu carrito está vacío</p>
        <p style="font-size: 0.9rem;">Agrega materiales desde el catálogo o la calculadora.</p>
      </div>
    `;
    if (totalAmountEl) totalAmountEl.innerText = '$0.00 MXN';
    if (grandTotalEl) grandTotalEl.innerText = '$0.00 MXN';
    return;
  }

  let subtotal = 0;

  container.innerHTML = cart.map(item => {
    const itemSubtotal = item.quantity * item.price;
    subtotal += itemSubtotal;
    return `
      <div class="cart-item-row">
        <div class="cart-item-info">
          <h4>${item.name}</h4>
          <p>$${item.price.toFixed(2)} por ${item.unit}</p>
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
          <div class="quantity-control" style="margin: 0;">
            <button class="qty-btn" onclick="window.updateCartQty(${item.id}, ${item.quantity - 1})">-</button>
            <input type="number" class="qty-input" value="${item.quantity}" onchange="window.updateCartQty(${item.id}, this.value)" />
            <button class="qty-btn" onclick="window.updateCartQty(${item.id}, ${item.quantity + 1})">+</button>
          </div>
          <div style="font-weight: 800; min-width: 90px; text-align: right;">
            $${itemSubtotal.toFixed(2)}
          </div>
          <button style="background: none; border: none; color: var(--accent-red); cursor: pointer; font-size: 1.1rem;" onclick="window.removeCartItem(${item.id})">
            🗑️
          </button>
        </div>
      </div>
    `;
  }).join('');

  const shipping = subtotal > 0 ? 150.00 : 0.00; // Flete base Neza
  const grandTotal = subtotal + shipping;

  if (totalAmountEl) totalAmountEl.innerText = `$${subtotal.toFixed(2)} MXN`;
  if (shippingCostEl) shippingCostEl.innerText = `$${shipping.toFixed(2)} MXN`;
  if (grandTotalEl) grandTotalEl.innerText = `$${grandTotal.toFixed(2)} MXN`;
}

// Global functions for inline HTML events
window.updateCartQty = (id, newQty) => updateCartQuantity(id, parseFloat(newQty));
window.removeCartItem = (id) => removeFromCart(id);

function showOrderConfirmationModal(order, deliveryMethod) {
  const modal = document.getElementById('order-success-modal');
  if (!modal) return;

  document.getElementById('order-folio').innerText = `#NEZA-${order.id}`;
  document.getElementById('order-client').innerText = order.client_name;
  document.getElementById('order-total').innerText = `$${Number(order.total).toFixed(2)} MXN`;
  document.getElementById('order-delivery').innerText = deliveryMethod === 'flete_neza' ? '🚚 Envío a Domicilio en Nezahualcóyotl' : '🏪 Recolección en Tienda Neza';

  modal.classList.add('active');

  const closeBtn = document.getElementById('order-modal-close');
  if (closeBtn) {
    closeBtn.onclick = () => modal.classList.remove('active');
  }
}
