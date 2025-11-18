/************************************************************
  FoodFlow - Final main.js
  Features:
  ✔ Load restaurants
  ✔ Show menu
  ✔ Add to cart
  ✔ Load orders
  ✔ Cancel orders (Admin/Manager only)
  ✔ Checkout (Admin/Manager only)
  ✔ Payment modal
  ✔ Add payment (Admin only)
  ✔ Currency based on country (₹ for India, $ for USA)
************************************************************/

document.addEventListener("DOMContentLoaded", () => {
  refreshAll();

  // Show username in header
  const userLabel = document.getElementById("userLabel");
  if (userLabel && window.USER_NAME) {
    userLabel.innerText = `👤 ${window.USER_NAME}`;
  }

  // Hide payment panel for non-admin
  if (window.USER_ROLE !== "admin") {
    const panel = document.getElementById("paymentPanel");
    if (panel) panel.style.display = "none";
  }

  // Members cannot checkout
  if (window.USER_ROLE === "member") {
    const btn = document.getElementById("checkoutBtn");
    if (btn) btn.style.display = "none";
  }
});


/************************************************************
  CURRENCY SUPPORT
************************************************************/
const COUNTRY_CURRENCY = {
  "India": "₹",
  "America": "$"
};

function getCurrency(country) {
  return COUNTRY_CURRENCY[country] || "$";
}

/************************************************************
  GLOBAL LOAD
************************************************************/
async function refreshAll() {
  await Promise.all([loadRestaurants(), loadOrders()]);
}

/************************************************************
  LOAD RESTAURANTS + MENUS  (WITH DIFFERENT IMAGES)
************************************************************/
async function loadRestaurants() {
  const container = document.getElementById("restaurants");
  if (!container) return;

  container.innerHTML = "Loading restaurants...";

  try {
    const res = await fetch("/api/restaurants");
    const restaurants = await res.json();

    container.innerHTML = "";

    // 🔥 Hardcoded images for each restaurant
    const images = [
      "/static/img/rest1.jpg",
      "/static/img/rest2.jpg",
      "/static/img/rest3.jpg",
      "/static/img/rest4.jpg",
      "/static/img/rest5.jpg",
      "/static/img/rest6.jpg"
    ];

    restaurants.forEach((r, index) => {

      // UI-level country restriction
      if (window.USER_ROLE !== "admin" && r.country !== window.USER_COUNTRY) {
        return;
      }

      // Pick the image (loops if restaurants > images)
      const imgSrc = images[index % images.length];

      const card = document.createElement("div");
      card.className = "restaurant-card";

      card.innerHTML = `
        <img src="${imgSrc}" class="thumb">

        <h3>${r.name}</h3>
        <div class="badge">${r.country}</div>

        <h4>Menu</h4>
        ${r.menu.map(item => `
          <div class="menu-item">
            <span>${item.name} - ${getCurrency(r.country)}${item.price}</span>
            <button class="btn-small btn-primary" onclick="addToCart(${r.id}, ${item.id})">Add</button>
          </div>
        `).join("")}
      `;

      container.appendChild(card);
    });

  } catch (err) {
    container.innerHTML = "Error loading restaurants.";
    console.error(err);
  }
}

/************************************************************
  ADD TO CART
************************************************************/
async function addToCart(restaurantId, itemId) {
  try {
    await fetch("/api/cart/add", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        restaurant_id: restaurantId,
        menu_item_id: itemId,
        qty: 1
      })
    });
  } catch (e) {
    console.error(e);
  }

  loadOrders();
}

/************************************************************
  LOAD ORDERS / CART
************************************************************/
async function loadOrders() {
  const box = document.getElementById("myorders");
  if (!box) return;

  box.innerHTML = "Loading orders...";

  try {
    const res = await fetch("/api/myorders");
    const orders = await res.json();

    if (!orders.length) {
      box.innerHTML = "No orders yet.";
      return;
    }

    box.innerHTML = "";

    orders.forEach(o => {
      const div = document.createElement("div");
      div.className = "order-item";

      const currency = getCurrency(o.country || window.USER_COUNTRY);

      div.innerHTML = `
        <div>
          <div class="meta">Order #${o.id}</div>
          <div class="meta">${o.items.map(i => `${i.name} x${i.qty}`).join(", ")}</div>
          <div class="meta">Added by: ${o.added_by || "Unknown"}</div>
          ${o.cancelled_by ? `<div class="meta">Cancelled by: ${o.cancelled_by}</div>` : ""}

          <div class="meta">${currency}${o.total}</div>
        </div>

        <div>
          ${
            o.status !== "cancelled" &&
            window.USER_ROLE !== "member"
              ? `<button class="btn-small btn-ghost" onclick="cancelOrder(${o.id})">Cancel</button>`
              : `<span class="meta">(${o.status})</span>`
          }
        </div>
      `;

      box.appendChild(div);
    });

  } catch (e) {
    box.innerHTML = "Error loading orders.";
    console.error(e);
  }
}

/************************************************************
  CANCEL ORDER
************************************************************/
async function cancelOrder(orderId) {
  if (window.USER_ROLE === "member") {
    alert("Members cannot cancel orders.");
    return;
  }

  try {
    await fetch(`/api/order/${orderId}/cancel`, { method: "POST" });
  } catch (e) { console.error(e); }

  loadOrders();
}

/************************************************************
  CHECKOUT
************************************************************/
let CURRENT_ORDER_ID = null;

async function openCheckoutCart() {
  if (window.USER_ROLE === "member") {
    alert("Members cannot checkout.");
    return;
  }

  try {
    const res = await fetch("/api/myorders");
    const orders = await res.json();

    const cart = orders.find(o => o.status === "cart");

    if (!cart) return alert("Your cart is empty.");

    CURRENT_ORDER_ID = cart.id;
    openPaymentModal();

  } catch (e) {
    console.error(e);
  }
}

/************************************************************
  PAYMENT MODAL (Selection)
************************************************************/
async function openPaymentModal() {
  const sel = document.getElementById("payment-selector");

  const res = await fetch("/api/payment-methods");
  const methods = await res.json();

  sel.innerHTML = methods
    .map(m => `<option value="${m.id}">${m.method_name} - ${m.card_last4}</option>`)
    .join("");

  document.getElementById("payment-modal").classList.remove("hidden");
}

async function submitPayment() {
  const pmId = document.getElementById("payment-selector").value;

  try {
    await fetch("/api/checkout", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        order_id: CURRENT_ORDER_ID,
        payment_method_id: pmId
      })
    });
  } catch (e) { console.error(e); }

  closeModal();
  loadOrders();
}

function closeModal() {
  document.getElementById("payment-modal").classList.add("hidden");
}

/************************************************************
  ADD PAYMENT METHOD (ADMIN ONLY)
************************************************************/
function showAddPaymentModal() {
  if (window.USER_ROLE !== "admin") return;
  document.getElementById("add-payment-modal").classList.remove("hidden");
}

function closeAddPaymentModal() {
  document.getElementById("add-payment-modal").classList.add("hidden");
}

async function savePaymentMethod() {
  const name = document.getElementById("pm-name").value;
  const last4 = document.getElementById("pm-last4").value;

  try {
    await fetch("/api/payment-methods", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        method_name: name,
        card_last4: last4
      })
    });
  } catch (e) { console.error(e); }

  closeAddPaymentModal();
}
