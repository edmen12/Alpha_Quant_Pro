# AlphaQuantPro Setup Creator
# Creates a self-extracting installer

$sourceFolder = "AlphaQuantPro_Portable"
$installerScript = "Install_AlphaQuant.bat"
$outputExe = "AlphaQuantPro_Setup.exe"

Write-Host "Creating self-extracting installer..." -ForegroundColor Green

# Create a compressed archive
Compress-Archive -Path $sourceFolder, $installerScript -DestinationPath "temp_package.zip" -Force

# Read the zip file
$zipBytes = [System.IO.File]::ReadAllBytes("temp_package.zip")
$zipBase64 = [Convert]::ToBase64String($zipBytes)

# Create the self-extracting script
$sfxScript = @"
`$ErrorActionPreference = 'Stop'
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Alpha Quant Pro - 安装程序" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Decode and extract
Write-Host "正在解压文件..." -ForegroundColor Yellow
`$zipData = [Convert]::FromBase64String('$zipBase64')
`$tempZip = "`$env:TEMP\alphaquant_install.zip"
[System.IO.File]::WriteAllBytes(`$tempZip, `$zipData)

`$extractPath = "`$env:TEMP\AlphaQuant_Install"
if (Test-Path `$extractPath) { Remove-Item `$extractPath -Recurse -Force }
Expand-Archive -Path `$tempZip -DestinationPath `$extractPath -Force

# Run installer
Write-Host "正在安装..." -ForegroundColor Yellow
Set-Location `$extractPath
& cmd /c Install_AlphaQuant.bat

# Cleanup
Remove-Item `$tempZip -Force
Write-Host ""
Write-Host "安装完成！" -ForegroundColor Green
Read-Host "按任意键退出"
"@

# Save as PS1
$sfxScript | Out-File -FilePath "sfx_installer.ps1" -Encoding UTF8

# Convert PS1 to EXE using PowerShell
Write-Host "Converting to EXE..." -ForegroundColor Yellow
powershell -Command "& {Set-ExecutionPolicy Bypass -Scope Process; Invoke-Expression (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/MScholtes/PS2EXE/master/PS2EXE.ps1'); ps2exe -inputFile sfx_installer.ps1 -outputFile $outputExe -noConsole:$false}"

if (Test-Path $outputExe) {
    $size = (Get-Item $outputExe).Length / 1MB
    Write-Host ""
    Write-Host "✅ Setup created: $outputExe ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create EXE. Keeping PowerShell script." -ForegroundColor Red
}

# Cleanup temp files
Remove-Item "temp_package.zip" -Force -ErrorAction SilentlyContinue
