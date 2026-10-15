/**
 * NezaMateriales — Capa de datos del frontend.
 *
 * El backend FastAPI corre en Cloud Run; Firebase Hosting reenvía /api/**
 * hacia ese servicio vía rewrite (ver firebase.json), por lo que en producción
 * queda como mismo origen y API_BASE puede seguir siendo relativo ('/api').
 * USE_REMOTE_API=false sirve como respaldo local sin backend (usa data.js).
 */

import { PRODUCTS } from './data.js';

const USE_REMOTE_API = true;
const API_BASE = '/api';

export async function fetchProducts(category = null) {
  if (!USE_REMOTE_API) {
    if (category && category !== 'Todos') {
      return PRODUCTS.filter((p) => p.category === category);
    }
    return PRODUCTS;
  }

  let url = `${API_BASE}/products`;
  if (category && category !== 'Todos') {
    url += `?category=${encodeURIComponent(category)}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Error al cargar la lista de productos');
  }
  return await response.json();
}

export async function fetchProductDetail(id) {
  if (!USE_REMOTE_API) {
    const product = PRODUCTS.find((p) => p.id === id);
    if (!product) {
      throw new Error(`Error al obtener detalle del producto #${id}`);
    }
    return product;
  }

  const response = await fetch(`${API_BASE}/products/${id}`);
  if (!response.ok) {
    throw new Error(`Error al obtener detalle del producto #${id}`);
  }
  return await response.json();
}

export async function createQuoteAPI(quotePayload) {
  if (!USE_REMOTE_API) {
    const folio = Math.floor(1000 + Math.random() * 9000);
    const items = quotePayload.items.map((item, idx) => {
      const product = PRODUCTS.find((p) => p.id === item.product_id);
      return {
        id: idx + 1,
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price,
        subtotal: item.quantity * item.unit_price,
        product_name: product ? product.name : `Material ID ${item.product_id}`,
      };
    });
    const total = items.reduce((sum, it) => sum + it.subtotal, 0);
    return {
      id: folio,
      client_name: quotePayload.client_name,
      description: `Pedido registrado en NezaMateriales (${quotePayload.delivery_method})`,
      total,
      created_at: new Date().toISOString(),
      items,
    };
  }

  const response = await fetch(`${API_BASE}/quotes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(quotePayload),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.message || 'Error al guardar la cotización');
  }
  return await response.json();
}
