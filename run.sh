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

read -r -p "Term to monitor, format example: Fall Term 2026 [Fall Term 2026]: " target_term_answer
if [ -z "$target_term_answer" ]; then
    export TARGET_TERM="Fall Term 2026"
else
    export TARGET_TERM="$target_term_answer"
fi

read -r -p "Course to monitor, format example: CMPUT 328 [CMPUT 328]: " target_course_answer
if [ -z "$target_course_answer" ]; then
    export TARGET_COURSE="CMPUT 328"
else
    export TARGET_COURSE="$target_course_answer"
fi

read -r -p "Auto-enter enrollment page when an open seat is found? [y/N]: " auto_enter_answer
case "$auto_enter_answer" in
    [Yy]|[Yy][Ee][Ss])
        export AUTO_ENTER_ENROLLMENT=true
        ;;
    *)
        export AUTO_ENTER_ENROLLMENT=false
        ;;
esac

echo "TARGET_TERM=$TARGET_TERM"
echo "TARGET_COURSE=$TARGET_COURSE"
echo "AUTO_ENTER_ENROLLMENT=$AUTO_ENTER_ENROLLMENT"

python beartracks-watch.py
