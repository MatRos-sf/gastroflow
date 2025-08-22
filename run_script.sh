#!/usr/bin/env bash
set -euo pipefail

# === KONFIG ===
WORKDIR="$HOME/apps/myproj"         # <- ścieżka do katalogu z manage.py
BRANCH="main"                       # <- gałąź gita
VENV="$WORKDIR/venv"                # <- ścieżka do venv
PORT="8000"                         # <- port dla runserver
LOGDIR="$WORKDIR/logs"
REQ="$WORKDIR/requirements.txt"
HASHFILE="$WORKDIR/.requirements.sha256"

# === LOGI ===
mkdir -p "$LOGDIR"
exec >>"$LOGDIR/boot_$(date +%F).log" 2>&1
echo "=== Boot $(date) ==="

# Czasem sieć wstaje chwilę po cronie
sleep 10

# === GIT ===
cd "$WORKDIR"
if [ -d .git ]; then
  echo "[git] fetch & fast-forward to $BRANCH"
  git fetch --all
  git checkout "$BRANCH"
  git pull --ff-only
else
  echo "Błąd: $WORKDIR nie jest repozytorium gita" >&2
  exit 1
fi

# === VENV ===
if [ ! -x "$VENV/bin/python" ]; then
  echo "[venv] tworzenie venv"
  python3 -m venv "$VENV"
fi
# aktywacja (dla skryptu nie jest konieczna, ale nie szkodzi)
# shellcheck disable=SC1091
source "$VENV/bin/activate"

"$VENV/bin/python" -V
"$VENV/bin/pip" install --upgrade pip

# === requirements tylko gdy się zmienił ===
if [ -f "$REQ" ]; then
  NEW_HASH="$(sha256sum "$REQ" | awk '{print $1}')"
  OLD_HASH="$(cat "$HASHFILE" 2>/dev/null || echo "")"
  if [ "$NEW_HASH" != "$OLD_HASH" ]; then
    echo "[pip] instalacja z requirements.txt (wykryta zmiana)"
    "$VENV/bin/pip" install -r "$REQ"
    echo "$NEW_HASH" > "$HASHFILE"
  else
    echo "[pip] pomijam instalację (brak zmian w requirements.txt)"
  fi
fi

# (opcjonalnie) migracje/statyczne
# "$VENV/bin/python" manage.py migrate --noinput
# "$VENV/bin/python" manage.py collectstatic --noinput

# === uruchomienie serwera ===
# zabij ewentualny poprzedni devserver
pkill -f "manage.py runserver" || true

echo "[django] start runserver na 0.0.0.0:${PORT}"
nohup "$VENV/bin/python" manage.py runserver 0.0.0.0:"$PORT" >/dev/null 2>&1 & disown

echo "[ok] gotowe."
