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

Use the built-in management command to create both accounts on first deployment:

```bash
python manage.py create_users
```

Credentials are read from environment variables by default (see `.env` configuration below). You can override them via CLI arguments:

```bash
python manage.py create_users \
    --boss_username admin \
    --boss_password secret \
    --workers_username staff \
    --workers_password staffpass
```

If a user already exists, the command skips creation and prints a warning — it is safe to run multiple times.

### Environment variables

Configure the following in your `.env` file:

```env
BOSS_USERNAME=Boss
BOSS_PASSWORD=your-secure-boss-password

WORKERS_USERNAME=Workers
WORKERS_PASSWORD=your-secure-workers-password
```
