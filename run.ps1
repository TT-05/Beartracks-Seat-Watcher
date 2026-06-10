if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Running setup..."
    python -m venv venv
    . .\venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    python -m playwright install chrome
} else {
    . .\venv\Scripts\Activate.ps1
}

if (-not (Test-Path ".env")) {
    Write-Host ".env not found. Starting Telegram setup..."
    python setup_telegram.py
}

$targetTermAnswer = Read-Host "Term to monitor, format example: Fall Term 2026 [Fall Term 2026]"
if ([string]::IsNullOrWhiteSpace($targetTermAnswer)) {
    $env:TARGET_TERM = "Fall Term 2026"
} else {
    $env:TARGET_TERM = $targetTermAnswer
}

$targetCourseAnswer = Read-Host "Course to monitor, format example: CMPUT 328 [CMPUT 328]"
if ([string]::IsNullOrWhiteSpace($targetCourseAnswer)) {
    $env:TARGET_COURSE = "CMPUT 328"
} else {
    $env:TARGET_COURSE = $targetCourseAnswer
}

$autoEnterAnswer = Read-Host "Auto-enter enrollment page when an open seat is found? [y/N]"
if ($autoEnterAnswer -match "^(?i:y|yes)$") {
    $env:AUTO_ENTER_ENROLLMENT = "true"
} else {
    $env:AUTO_ENTER_ENROLLMENT = "false"
}

Write-Host "TARGET_TERM=$env:TARGET_TERM"
Write-Host "TARGET_COURSE=$env:TARGET_COURSE"
Write-Host "AUTO_ENTER_ENROLLMENT=$env:AUTO_ENTER_ENROLLMENT"

python beartracks-watch.py
