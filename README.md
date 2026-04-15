# GastroFlow

A Django-based restaurant management system with real-time order tracking for kitchen and bar staff.

---

## User Model

GastroFlow uses two application-level accounts instead of individual user accounts per employee:

### Boss
A superuser account for the restaurant manager. The Boss can manage workers, menu items, orders, and access all reports. Credentials are configured via environment variables.

### Workers
A single shared account used by all floor staff (waiters, chefs, baristas). Because multiple real employees share this login, individual workers are tracked via the **Worker** model (with `first_name`, `last_name`, `position`, and an optional 4-digit `pin`), not via separate Django users.

| Account | Django superuser | Who uses it |
|---------|-----------------|-------------|
| Boss    | Yes             | Restaurant manager |
| Workers | No              | Waiters, chefs, baristas |

---

## Setup — Creating User Accounts

GastroFlow runs inside Docker. Use `docker compose exec` to run management commands inside the running container.

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

**Step 2 — Run the command:**

```bash
docker compose exec web python manage.py create_menu /app/menu.json
```

The file path must be a path inside the container, not your local machine. After copying with `docker compose cp`, the file is available at the path you specified (in this example `/app/menu.json`).

---

## Fiscal Printer (POSNET)

GastroFlow has an integration with POSNET fiscal printers for printing receipts.

> This feature is experimental and was only tested in simulation (developer) mode.

For setup instructions, configuration, and how to get receipt images in development, see [`posnet/README.md`](posnet/README.md).
