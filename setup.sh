#!/bin/bash

echo "Setting up Bear Tracks Seat Watcher..."

python3 -m venv venv

source venv/bin/activate

pip install --upgrade pip

pip install -r requirements.txt

python -m playwright install chrome

echo ""

echo "Setup complete."

echo ""

echo "Next steps:"

echo "1. Activate the virtual environment:"

echo "   source venv/bin/activate"

echo ""

echo "2. Set up Telegram:"

echo "   python setup_telegram.py"

echo ""

echo "3. Run the watcher:"

echo "   python beartracks-watch.py"
