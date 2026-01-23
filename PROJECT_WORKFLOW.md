# Trading App – Project Workflow Documentation (2024–2025

---

## Table of Contents

1.  [Project Overview](#project-overview)
2.  [System Architecture](#system-architecture)
3.  [Core Components](#core-components)
4.  [Data Models & Relationships](#data-models--relationships)
5.  [Application Flow](#application-flow)
6.  [User Journeys](#user-journeys)
7.  [Technology Stack & Tooling](#technology-stack--tooling)
8.  [Database Schema](#database-schema)
9.  [Feature Calculations & Logic](#feature-calculations--logic)
10. [Security Practices](#security-practices)
11. [Roadmap & Enhancements](#roadmap--enhancements)
12. [Summary](#summary)

---

## Project Overview

The **Trading App** is a modern, Django-powered platform for portfolio tracking and trade analytics. Key capabilities for authenticated users include:

- Live stock price display  
- Buy/sell/order tracking  
- Portfolio statistics (profit/loss, history, summary)  
- Risk controls (target/stop-loss)  
- Interactive dashboards with sorting/filtering

---

## System Architecture

Built on Django's **Model-View-Template (MVT)** paradigm with a modular, maintainable codebase:

```
┌─────────────────────────────┐
│   Client (Browser)          │
└─────────────┬───────────────┘
              │ HTTPS
┌─────────────▼───────────────┐
│     Django URLs (urls.py)   │
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│     Views (views.py)        │
│  - Auth / permissions       │
│  - Logic, ORM, processing   │
└───────┬───────────────┬─────┘
        │               │
┌───────▼─────┐     ┌───▼─────────┐
│ forms.py    │     │ models.py   │
│ - Validation      │- ORM models │
│ - Bootstrap UX    │- Business   │
└─────────────┘     │  logic      │
                   └────┬────────┘
                        │
           ┌────────────▼─────────────┐
           │      MySQL or MariaDB    │
           └──────────────────────────┘
```

---

## Core Components

### 1. Models (`App/models.py`)

#### Stock Model
- Represents a stock/security
- Fields:  
    - `symbol` (unique), `name`, `current_price`
    - Targets: `tp1`–`tp3`
    - Stops: `sl1`–`sl3`
    - Indicators: `rsi`, `ltp1`–`ltp3`, `low`, `high`
    - `created_at`

#### Trade Model
- Represents a user's trade
- Fields:  
    - Foreign keys: `user`, `stock`
    - Trade info: `quantity`, `buying_price`, `buy_date`
    - Risk: `mtp`, `msl`
    - Calculations: `profit_expected`, `loss_expected`, `pl_ratio`, etc.
    - Runtime/calculated: `total_cost`, `current_value`, `unrealized_pl`, `pl_percent`
- Derived values auto-updated on `save()`

### 2. Views (`App/views.py`)

- **Auth:**  
    - `home_view` (redirects if logged in)
    - Standard Django `LoginView`, `LogoutView`
- **Stock Views:**  
    - Paginated list (25/page)
    - Full CRUD (add, detail, edit, delete w/ confirm)
- **Trade Views:**  
    - Add (auto-user linkage)
    - User-owned list
    - Update (ownership enforced), delete
- **Portfolio:**  
    - Dashboard view with analytics, filters, and protected by `@login_required`

### 3. Forms (`App/forms.py`)

- `StockForm`: Full ModelForm for stocks
- `TradeForm`: Restricted ModelForm  
    - Validation (ex. positive quantity)
    - Bootstrap enhanced

### 4. URL Routing (`App/urls.py`)

 _____________________________________________________________________________________
| URL Path                   | View Function         | Description                   |
|----------------------------|----------------------|-------------------------------|
| `/`                        | `home_view`          | Home/redirection              |
| `/login/`                  | `LoginView`          | Login page                    |
| `/logout/`                 | `LogoutView`         | Logout action                 |
| `/stocks/`                 | `stock_list_view`    | Stock master list             |
| `/stocks/add/`             | `stock_create_view`  | Add new stock                 |
| `/stocks/<pk>/`            | `stock_detail_view`  | Stock details                 |
| `/stocks/<pk>/edit/`       | `stock_update_view`  | Update stock                  |
| `/stocks/<pk>/delete/`     | `stock_delete_view`  | Remove stock                  |
| `/trades/`                 | `trade_list_view`    | User's trades                 |
| `/trades/add/`             | `trade_create_view`  | Place new trade               |
| `/trades/<pk>/edit/`       | `trade_update_view`  | Edit trade                    |
| `/trades/<pk>/delete/`     | `trade_delete_view`  | Remove trade                  |
| `/portfolio/`              | `portfolio_dashboard`| Performance dashboard         |
 ─────────────────────────────────────────────────────────────────────────────────────

### 5. Templates (`App/templates/App/`)

- `base.html`, `login.html`
- `stocks/`: list, detail, form, delete
- `trades/`: list, form, delete
- `portfolio/`: dashboard

---

## Data Models & Relationships

### Entity-Relationship Diagram

```
┌──────────┐      ┌──────────┐
│  User    │      │  Stock   │
└─────┬────┘      └─────┬────┘
      │                 │
     1:N               1:N
      │                 │
      └───────┬ ────────┘
              ▼
           Trade
```

- **Trade** associates one `User` with stocks they're trading.

**Relationships:**

- User–Trade: One user, many trades
- Stock–Trade: One stock, many trades

---

## Application Flow

**Create Stock:**
```
User ⟶ stock_create_view ⟶ StockForm.validate
     ⟶ Stock.save()
     ⟶ DB
     ⟶ Redirect: stock_list
```

**Create Trade:**
```
User ⟶ trade_create_view ⟶ TradeForm.validate
     ⟶ trade.user = request.user
     ⟶ Trade.save() (auto-calculated)
     ⟶ DB
     ⟶ Redirect: trade_list
```

**Portfolio Dashboard:**
```
User ⟶ portfolio_dashboard
   ⟶ Query: Trade.objects.filter(user=...)
   ⟶ Filters/sorting (symbol, date, P/L)
   ⟶ Aggregates: sum(total_cost), sum(current_value), P/L %
   ⟶ Render Dashboard
```

**Trade Update:**
```
User ⟶ trade_update_view
   ⟶ Check ownership
   ⟶ TradeForm(instance)
   ⟶ Trade.save() (recalculates)
   ⟶ DB, redirect
```

**Authentication:**
```
If not logged in ⟶ @login_required
                ⟶ Redirect: /login/
                ⟶ LoginView, session
                ⟶ Redirect: LOGIN_REDIRECT_URL (/stocks/)
```

---

## User Journeys

### 1. Onboarding & Placing a First Trade

- Land on `/` (home), log in or redirect
- Browse stocks, place trade
- Trades instantly tied to current user; analytics calculated on save
- Portfolio dashboard summarizes invested positions

### 2. Trade Management

- See only own trades, paginated
- Edit (auto-recalculate P/L), delete (with confirm)

### 3. Stock Management

- Add stocks with all major info
- Update price triggers live dashboard refresh for all users

---

## Technology Stack & Tooling

- **Backend:**  
    - Django 4.2+ (Python 3.x)  
    - MySQL (with `mysqlclient` or `PyMySQL`)  
    - Gunicorn (WSGI)
- **Frontend:**  
    - Django Templates (DTL)  
    - Bootstrap (CSS/Layout)  
    - Minimal JS
- **Dev Tools:**  
    - python-decouple (.env configs)  
    - Docker + Compose  
    - pip (`requirements.txt`)
- **Security:**  
    - Django Auth (sessions, CSRF, `@login_required`), validation

---

## Database Schema

**Stock Table**
```sql
CREATE TABLE App_stock (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    current_price DECIMAL(10,2) NOT NULL,
    tp1 DECIMAL(10,2), tp2 DECIMAL(10,2), tp3 DECIMAL(10,2),
    sl1 DECIMAL(10,2), sl2 DECIMAL(10,2), sl3 DECIMAL(10,2),
    rsi DECIMAL(5,2),
    ltp1 DECIMAL(10,2), ltp2 DECIMAL(10,2), ltp3 DECIMAL(10,2),
    low DECIMAL(10,2), high DECIMAL(10,2),
    created_at DATETIME NOT NULL
);
```

**Trade Table**
```sql
CREATE TABLE App_trade (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    stock_id BIGINT NOT NULL,
    quantity INT UNSIGNED NOT NULL,
    buying_price DECIMAL(10,2) NOT NULL,
    buy_date DATE NOT NULL,
    mtp DECIMAL(10,2), msl DECIMAL(10,2),
    profit_expected DECIMAL(10,2),
    profit_percent DECIMAL(5,2),
    loss_expected DECIMAL(10,2),
    loss_recent DECIMAL(10,2),
    pl_ratio DECIMAL(5,2),
    rate_difference DECIMAL(10,2),
    pl_percent DECIMAL(5,2),
    comments TEXT,
    max_profit DECIMAL(10,2),
    min_profit_loss DECIMAL(10,2),
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_id) REFERENCES App_stock(id) ON DELETE CASCADE
);
```

---

## Feature Calculations & Logic

- **Profit Expected:**      `(mtp - buying_price) * quantity`
- **Profit Percent:**       `((mtp - buying_price) / buying_price) * 100`
- **Loss Expected:**        `(buying_price - msl) * quantity`
- **P/L Ratio:**            `(mtp - buying_price) / (buying_price - msl)`
- **Rate Difference:**      `current_price - buying_price`
- **Loss (Recent):**        If `current_price < buying_price` and meets MSL, then `(buying_price - current_price) * quantity`

**Portfolio Metrics:**
- **Total Cost:**      Sum of (`quantity * buying_price`)
- **Total Value:**     Sum of (`quantity * current_price`)
- **Unrealized P/L:**  `total_value - total_cost`
- **P/L Percentage:**  `(unrealized_pl / total_cost) * 100`

---

## Security Practices

1. **Authentication:**     All but home requires login.
2. **Authorization:**      Users only access their own trades.
3. **CSRF Protection:**    Enabled on all forms.
4. **SQL Injection:**      Prevented via Django ORM.
5. **Validation:**         Strict checks server- and client-side.
6. **Isolation:**          Per-user database scoping.

---

## Roadmap & Enhancements

- Celery jobs (async stock sync, notifications)
- Redis (performance caching)
- Time-series price logs (`max_profit`, `min_profit_loss`)
- REST API endpoints (in progress)
- Enhanced mobile responsiveness

---

## Summary

The Trading App is a Django-based portfolio tracker and trading manager designed for secure, accurate finance calculation and user-centric dashboards. Its layered architecture, strict user auth, and fully calculated analytics offer strong structure today with extensibility for API and automation in the future.

