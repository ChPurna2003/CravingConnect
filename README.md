# 🍽️ FoodFlow — Role-Based Food Ordering System (Flask)

FoodFlow is a full-stack food ordering system built using **Flask**, featuring:

- Dark Premium UI (HTML + CSS + JS)
- Restaurants & Menu
- Cart & Orders
- Payment Methods
- Role-Based Access Control (RBAC)
- Country-Level Restriction (BONUS requirement)
- Admin, Manager, Member workflows

---

# 🚀 Features

## ✔ For All Users
- Login
- View restaurants in their allowed country
- View menu items
- Add items to cart

## ✔ Admin
- Can view **all** restaurants (all countries)
- Can add items to cart
- Can checkout orders
- Can cancel any order
- Can add payment methods
- Can modify payment methods
- Can see all orders (`?all=1`)
- Unrestricted country access

## ✔ Manager
- Can view restaurants **only in their country**
- Can add items to cart
- Can checkout orders
- Can cancel orders in their country
- Cannot update payment methods (only own)
- Restricted to their assigned country

## ✔ Member
- Can view restaurants **only in their country**
- Can add items to cart
- Cannot checkout orders
- Cannot cancel orders
- Cannot modify payment methods
- Restricted to their assigned country

---

# 👤 **Seeded Users (Roles + Passwords)**

These users are created automatically when running `db_init.py`.

| Username          | Password  | Role     | Country  |
|------------------|-----------|----------|----------|
| **nick**          | password  | admin    | None     |
| **captain_marvel** | password  | manager  | India    |
| **captain_america** | password | manager  | America  |
| **thanos**         | password  | member   | India    |
| **thor**           | password  | member   | India    |
| **travis**         | password  | member   | America  |

---

# 🌍 Country Restrictions (Bonus)

- Managers can only operate in **their assigned country**
- Members can only see restaurants in **their assigned country**
- Admin bypasses all country restrictions

Examples:

| User             | Country | Allowed Restaurants       |
|------------------|---------|---------------------------|
| captain_marvel   | India   | Only restaurants in India |
| captain_america  | America | Only restaurants in USA   |
| thor             | India   | Only restaurants in India |
| nick (admin)     | All     | All countries             |

---

# 💲 Currency Support (Dynamic)
FoodFlow displays currency based on restaurant country:

| Country | Currency |
|---------|----------|
| India   | ₹        |
| America | $        |

---

✅ Admin
Username	Password	Country	Permissions
nick	password	None	Full access (all countries, all features)
🟦 Managers
Username	Password	Country	Permissions
captain_marvel	password	India	Manage restaurants & orders in India
captain_america	password	America	Manage restaurants & orders in America
🟩 Members
Username	Password	Country	Permissions
thanos	password	India	Customer (India only)
thor	password	India	Customer (India only)
travis	password	America	Customer (USA only)
