#!/bin/bash

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    python -m playwright install chrome
else
    source venv/bin/activate
fi

if [ ! -f ".env" ]; then
    echo ".env not found. Starting Telegram setup..."
    python setup_telegram.py
fi

python beartracks-watch.py
