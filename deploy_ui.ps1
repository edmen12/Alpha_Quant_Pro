$ErrorActionPreference = "Stop"

Write-Host "1. Building Next.js App..." -ForegroundColor Cyan
cd alpha-quant
npm run build
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "2. Deploying to web_ui..." -ForegroundColor Cyan
# Ensure destination exists
if (-not (Test-Path "../web_ui")) { New-Item -ItemType Directory -Path "../web_ui" }

# Copy content
Copy-Item -Path "out\*" -Destination "..\web_ui" -Recurse -Force

Write-Host "------------------------------------------------" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "Now start your Python Trading Terminal." -ForegroundColor White
Write-Host "The new UI will be available at: http://localhost:8000" -ForegroundColor White
Write-Host "------------------------------------------------" -ForegroundColor Green
