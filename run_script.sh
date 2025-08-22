#!/usr/bin/env bash
echo "1"
set -euo pipefail
echo "2"
cd "$HOME/Desktop/Frisztek/gastroflow"
sleep 10 
pkill -f "manage.py runserver" || true
git pull
. venv/bin/activate 
pip install -r requirements.txt

python manage.py runserver 0.0.0.0:8000
