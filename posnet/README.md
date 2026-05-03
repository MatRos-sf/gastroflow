# POSNET Fiscal Printer Integration

> **Warning:** This integration is **experimental**. It was only tested in developer (simulation) mode — never on a real fiscal printer in production.
>
> This is a hobby project. The author takes **no responsibility** for any legal, fiscal, or financial issues that may result from using this code. Fiscal printing is regulated by law in Poland. Always consult a professional before using this in a real restaurant.

---

## What is this?

GastroFlow uses **POSNET Server** — a Node.js application that communicates with POSNET fiscal printers over TCP/IP. When a bill is finalized, a Celery task builds the receipt payload and sends it to POSNET Server via HTTP.

In **simulation mode** (development), POSNET Server generates a PNG image of the receipt instead of printing it. No real printer is needed.

---

## Step 1 — Download the POSNET Server binary

The POSNET Server binary is **not included** in this repository. You need to download it manually.

1. Go to: https://blog.bigdotsoftware.pl/ingenico-server-instalacja/
2. Download the file: `posnetserver.x64.5.7-GLIBC-2.31.1201.tar.gz`
3. Place it in the `posnet/` directory (next to the `Dockerfile`)

Without this file, `docker compose build` will fail.

---

## Step 2 — Configure environment variables

Add these variables to your `.env` file:

```env
# Required — turn simulation on/off
POSNET_SIMULATION=True

# Your restaurant details (printed on the receipt in simulation)
COMPANY_NAME=Your Restaurant Name
ADDRESS=Your Street 1, 00-000 City

# Optional — defaults work for Docker
POSNET_URL=http://posnet:3020
POSNET_DEV_BILLS_DIR=/app/dev-bills
```

| Variable | Description | Default |
|---|---|---|
| `POSNET_SIMULATION` | `True` = generate PNG, `False` = print for real | `False` |
| `COMPANY_NAME` | Company name on receipt header | _(empty)_ |
| `ADDRESS` | Address on receipt header | _(empty)_ |
| `POSNET_URL` | Internal URL of POSNET Server in Docker | `http://posnet:3020` |
| `POSNET_DEV_BILLS_DIR` | Where to save PNG files in simulation mode | `/app/dev-bills` |

---

## Step 3 — Disable authentication (development only)

POSNET Server has authentication enabled by default. In development, disable it in `posnet/config.json`:

```json
"auth": {
    "active": false,
    ...
}
```

> **Note:** Do not disable authentication in production. If you plan to expose POSNET Server outside Docker, set up proper credentials using the `users_file` option.

After changing `config.json`, restart the container (no rebuild needed — the file is mounted as a volume):

```bash
docker compose restart posnet
```

---

## Step 4 — Build and run

```bash
docker compose build
docker compose up
```

The `posnet` service starts automatically. It is only accessible inside the Docker network — it has no public port by default.

---

## How to get receipt images (simulation mode)

In simulation mode, receipt PNG files are saved inside the `celery` container at `POSNET_DEV_BILLS_DIR` (default: `/app/dev-bills/`).

**List all saved receipts:**

```bash
docker compose exec celery ls /app/dev-bills/
```

**Copy a single receipt to your machine:**

```bash
docker compose cp celery:/app/dev-bills/bill_1.png ./bill_1.png
```

**Copy all receipts to your machine:**

```bash
docker compose cp celery:/app/dev-bills/ ./dev-bills/
```

Files are named `bill_{id}.png` where `{id}` is the Bill primary key.

---

## Full documentation

- Installation guide: https://blog.bigdotsoftware.pl/ingenico-server-instalacja/
- Full API documentation: https://blog.bigdotsoftware.pl/ingenico-server-wprowadzenie/
