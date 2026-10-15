/**
 * NezaMateriales — Módulo de Catálogo de Productos y Modal de Detalle
 */

import { fetchProducts } from './api.js';
import { addToCart } from './cart.js';
import { showToast } from './app.js';

let currentProducts = [];
let activeProductForModal = null;

export async function initCatalog() {
  const container = document.getElementById('products-grid');
  if (!container) return;

  try {
    currentProducts = await fetchProducts();
    renderCategories();
    renderProductCards(currentProducts);
  } catch (error) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--accent-red);">
        <p>⚠️ ${error.message}. Intenta recargar la página.</p>
      </div>
    `;
  }
}

function renderCategories() {
  const pillsContainer = document.getElementById('category-pills');
  if (!pillsContainer) return;

  const categories = ['Todos', ...new Set(currentProducts.map(p => p.category))];

  pillsContainer.innerHTML = categories.map((cat, idx) => `
    <button class="category-pill ${idx === 0 ? 'active' : ''}" data-category="${cat}">
      ${cat}
    </button>
  `).join('');

  pillsContainer.querySelectorAll('.category-pill').forEach(btn => {
    btn.addEventListener('click', (e) => {
      pillsContainer.querySelectorAll('.category-pill').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      const selectedCategory = e.target.dataset.category;
      
      const filtered = selectedCategory === 'Todos' 
        ? currentProducts 
        : currentProducts.filter(p => p.category === selectedCategory);
        
      renderProductCards(filtered);
    });
  });
}

function renderProductCards(products) {
  const container = document.getElementById('products-grid');
  if (!container) return;

  if (products.length === 0) {
    container.innerHTML = `<p style="grid-column: 1/-1; color: var(--text-muted);">No hay materiales en esta categoría.</p>`;
    return;
  }

  container.innerHTML = products.map(p => `
    <div class="product-card" data-id="${p.id}">
      <img class="product-thumb" src="${p.image_url}" alt="${p.name}" loading="lazy" />
      <div class="product-body">
        <span class="product-category-tag">${p.category || 'Construcción'}</span>
        <h3 class="product-title">${p.name}</h3>
        <p class="product-desc">${p.description}</p>
        <div class="product-footer">
          <div>
            <div class="product-price">$${Number(p.price).toFixed(2)}</div>
            <div class="product-unit">por ${p.unit}</div>
          </div>
          <button class="btn-detail">Ver detalle 🔍</button>
        </div>
      </div>
    </div>
  `).join('');

  container.querySelectorAll('.product-card').forEach(card => {
    card.addEventListener('click', () => {
      const prodId = parseInt(card.dataset.id, 10);
      const product = currentProducts.find(p => p.id === prodId);
      if (product) {
        openProductModal(product);
      }
    });
  });
}

export function openProductModal(product) {
  activeProductForModal = product;
  const modal = document.getElementById('product-modal');
  if (!modal) return;

  document.getElementById('modal-product-title').innerText = product.name;
  document.getElementById('modal-product-category').innerText = product.category || 'Material de Obra';
  document.getElementById('modal-product-img').src = product.image_url;
  document.getElementById('modal-product-desc').innerText = product.description;
  document.getElementById('modal-product-yield').innerText = product.yield_info || 'Rendimiento estándar según normas de construcción.';
  document.getElementById('modal-product-price').innerText = `$${Number(product.price).toFixed(2)}`;
  document.getElementById('modal-product-unit').innerText = `por ${product.unit}`;
  document.getElementById('modal-qty-input').value = 1;

  modal.classList.add('active');
}

export function initModalListeners() {
  const modal = document.getElementById('product-modal');
  const closeBtn = document.getElementById('modal-close-btn');
  const minusBtn = document.getElementById('modal-qty-minus');
  const plusBtn = document.getElementById('modal-qty-plus');
  const qtyInput = document.getElementById('modal-qty-input');
  const addBtn = document.getElementById('modal-add-cart-btn');

  if (closeBtn) {
    closeBtn.addEventListener('click', () => modal.classList.remove('active'));
  }
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('active');
    });
  }

  if (minusBtn && qtyInput) {
    minusBtn.addEventListener('click', () => {
      let val = parseInt(qtyInput.value, 10) || 1;
      if (val > 1) qtyInput.value = val - 1;
    });
  }
  if (plusBtn && qtyInput) {
    plusBtn.addEventListener('click', () => {
      let val = parseInt(qtyInput.value, 10) || 1;
      qtyInput.value = val + 1;
    });
  }

  if (addBtn) {
    addBtn.addEventListener('click', () => {
      if (!activeProductForModal) return;
      const qty = parseFloat(qtyInput.value) || 1;
      addToCart(activeProductForModal, qty);
      modal.classList.remove('active');
      showToast(`🛒 ${activeProductForModal.name} (${qty} ${activeProductForModal.unit}) agregado al carrito.`);
    });
  }
}
