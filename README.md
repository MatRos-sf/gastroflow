# GastroFlow

GastroFlow is a restaurant management system built with Django. It helps restaurant staff take orders, track their status in real time, manage the menu, and close bills — all from a browser.

The system has three main views running at the same time:
- **Waiter view** — take orders at the table, track notifications
- **Kitchen display** — see incoming food orders, mark them as ready
- **Bar display** — see incoming drink orders, mark them as ready

When a waiter places an order, the kitchen and bar screens update immediately using WebSockets — no page refresh needed.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django (no REST framework — plain views and forms) |
| Real-time | Django Channels + WebSockets |
| Async tasks | Celery |
| Message broker | Redis |
| Database | PostgreSQL (production) / SQLite (development) |
| Proxy / static | Nginx |
| Fiscal printer | POSNET integration via TCP/IP |
| Containerization | Docker + Docker Compose |

---

## How to Run with Docker

### 1. Clone the repository

```bash
git clone <repository-url>
cd gastroflow
```

### 2. Create your environment file

Copy the sample and fill in your values:

```bash
cp .env.sample .env
```

Open `.env` and set the following variables:

```env
# Django
SECRET_KEY=your-secret-key-here        # generate a long random string
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://localhost

# Database (must match POSTGRES_* values below)
DATABASE_URL=postgres://gastroflow:your-db-password@db:5432/gastroflow

# PostgreSQL container
POSTGRES_DB=gastroflow
POSTGRES_USER=gastroflow
POSTGRES_PASSWORD=your-db-password

# Redis (REDIS_PASSWORD must match the password in REDIS_URL)
REDIS_PASSWORD=your-redis-password
REDIS_URL=redis://:your-redis-password@redis:6379/0

# Email (used for sending reports)
HOST_EMAIL=your-email@gmail.com
HOST_PASSWORD=your-gmail-app-password

# Company info (printed on fiscal receipts)
COMPANY_NAME=YourCompanyName

# Port exposed by Nginx
WEB_PORT=80
```

> **Tip:** To generate a Django secret key, run:
> `python -c "import secrets; print(secrets.token_urlsafe(50))"`

### 3. Build and start all services

```bash
docker compose up --build -d
```

This command starts six services:
- `db` — PostgreSQL database
- `redis` — Redis (broker + cache)
- `web` — Django app (Daphne ASGI server, port 8000 internally)
- `celery` — Background task worker
- `posnet` — Fiscal printer service (internal only)
- `nginx` — Reverse proxy (public port from `WEB_PORT`)

Django automatically runs `collectstatic` and `migrate` on startup.

### 4. Create user accounts

```bash
docker compose exec web python manage.py create_users \
    --boss_username Boss \
    --boss_password your-boss-password \
    --workers_username Workers \
    --workers_password your-workers-password
```

### 5. Load the menu

Menu data is not included in the repository. You need a JSON file with your restaurant's menu.

Copy the file into the container and run the import command:

```bash
docker compose cp /path/to/your/menu.json web:/app/menu.json
docker compose exec web python manage.py create_menu /app/menu.json
```

### 6. Open the app

Go to `http://localhost` (or the port you set in `WEB_PORT`).

---

## Stopping and restarting

```bash
docker compose down          # stop containers (data is preserved in volumes)
docker compose down -v       # stop and delete all data (volumes)
docker compose up -d         # start again (no rebuild needed)
docker compose up --build -d # start and rebuild images (after code changes)
```

---

## How the Models Work

GastroFlow is organized into five main areas: orders, menu, service (tables), workers, and notifications.

### Menu

The menu has a simple hierarchy:

```
Category → SubCategory → Item
```

- **Category** — a top-level group, for example "Food" or "Drinks"
- **SubCategory** — a group inside a category, for example "Pasta" inside "Food"
- **Item** — a specific dish or drink that can be ordered
  - Has a `price`, `vat` rate, and `preparation_location` (KITCHEN or BAR)
  - Has `daily_stock` — `null` means unlimited, `0` means sold out
  - Can have **Additions** — extras like "extra sauce" or "side salad" (ManyToMany)
- **Addition** — an optional extra that a customer can add to an item

**MenuPeriod** links items to a time range (e.g. "Lunch menu: 11:00–15:00"). Items in a period only appear during that time window.

---

### Service (Tables and Halls)

The restaurant floor is organized like this:

```
Hall → Table
```

- **Hall** — a section of the restaurant (e.g. "Main room", "Terrace")
- **Table** — a physical table inside a hall
  - Has `x` and `y` position (percentage — used to render a visual floor map)
  - Has `is_occupied` to show if a bill is currently open

---

### Orders and Bills

This is the core of the system. The full order flow looks like this:

```
Table → Bill → Order → OrderItem → OrderItemAddition
```

- **Bill** — opened when a waiter starts serving a table
  - Links to one or more tables
  - Has a `status`: OPEN → CLOSED
  - Has `payment_method` (card, cash, or both) and optional `discount`
  - Is linked to the `Worker` (waiter) who opened it
- **Order** — a group of items sent to one location (KITCHEN or BAR)
  - One bill can have many orders (e.g. first round of drinks + second round of food)
  - Has a `status`: ORDER → PREPARING → READY → PAID / CANCELED
- **OrderItem** — a single line in an order (one item × quantity)
  - Stores `name_snapshot` and `price_snapshot` — the price at the time of ordering (so changing the menu later does not affect past orders)
  - Has its own `status`: WAITING → PREPARING → READY / CANCELED
- **OrderItemAddition** — an addition attached to a specific order item (e.g. "+extra cheese")
  - Also stores a price snapshot

---

### Workers

- **Worker** — one real employee (waiter, chef, barista, etc.)
  - All workers share one Django login (`Workers` account)
  - Individual tracking uses the `Worker` model with an optional 4-digit `pin`
- **WorkTime** — one shift (clock-in to clock-out)
  - Stores `salary_snapshot` so a pay rate change does not affect old shifts
  - Has `is_settled` to track if the shift was included in a payroll settlement

---

### Notifications

- **Notification** — a message sent to a worker
  - Type: `item_info` (item is ready), `order_info` (full order is ready), or `call` (table called for help)
  - Status: `none` → `waiting_to_read` → `read`
  - A red dot appears in the waiter's navigation bar when there are unread notifications

---

## User Model

GastroFlow uses two application-level accounts instead of individual user accounts per employee:

### Boss
A superuser account for the restaurant manager. The Boss can manage workers, menu items, orders, and access all reports.

### Workers
A single shared account used by all floor staff. Because multiple real employees share this login, individual workers are tracked via the `Worker` model (first name, last name, position, optional PIN) — not via separate Django users.

| Account | Django superuser | Who uses it |
|---------|-----------------|-------------|
| Boss    | Yes             | Restaurant manager |
| Workers | No              | Waiters, chefs, baristas |

---

## Setup — Creating User Accounts

Use the built-in management command to create the accounts on first deployment:

```bash
docker compose exec web python manage.py create_users \
    --boss_username Boss \
    --boss_password your-boss-password \
    --workers_username Workers \
    --workers_password your-workers-password
```

All four arguments are required. If you skip an account's arguments, that account will not be created.

**The command is safe to run multiple times.** If a user already exists, it is skipped — no data is changed.

---

## Setup — Loading the Menu

Menu data is not stored in the repository (it contains restaurant-specific information). You need to load it manually on first deployment.

**Step 1 — Copy your JSON file into the container:**

```bash
docker compose cp /path/to/your/menu.json web:/app/menu.json
```

**Step 2 — Run the import command:**

```bash
docker compose exec web python manage.py create_menu /app/menu.json
```

The file path must be a path inside the container. After copying with `docker compose cp`, the file is available at the path you specified.

---

## Fiscal Printer (POSNET)

GastroFlow has an integration with POSNET fiscal printers for printing receipts.

> This feature is experimental and was only tested in simulation (developer) mode.

For setup instructions, configuration, and how to get receipt images in development, see [`posnet/README.md`](posnet/README.md).
