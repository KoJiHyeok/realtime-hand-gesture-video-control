# 프로그램을 시작한다. 이미 실행 중이면 끄고 다시 켠다 (웹캠은 한 프로그램만 쓸 수 있다).
Set-Location $PSScriptRoot
Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "$PSScriptRoot\*" } |
    Stop-Process -Force

$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
& ".\.venv\Scripts\python.exe" run.py 2>&1 | Tee-Object run.log
