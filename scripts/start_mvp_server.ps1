$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "C:\Users\LENOVO\Documents\Codex\2026-04-21-codex\src"
& "C:\Users\LENOVO\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m uvicorn ashare_strategy.api:app --host 127.0.0.1 --port 8000

