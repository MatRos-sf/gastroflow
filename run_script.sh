#!/usr/bin/env bash
set -euo pipefail
echo "Hello"
# 1. Definiowanie ścieżek
LOG_DIR="$HOME/Desktop/log_frisztek"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"

# 2. Tworzenie katalogu, jeśli nie istnieje
mkdir -p "$LOG_DIR"

# 3. Przekierowanie całego skryptu do pliku logów
exec >> "$LOG_FILE" 2>&1

echo "---"
echo "Skrypt uruchomiony: $(date)"
echo "---"

# 4. Reszta twojego oryginalnego skryptu
cd "$HOME/Desktop/Frisztek/gastroflow"

sleep 10

pkill -f "manage.py runserver" || true
git pull
. venv/bin/activate
pip install -r requirements.txt

echo "start redis"
docker start redis
echo "redis started"
python3 manage.py runserver 0.0.0.0:8000
