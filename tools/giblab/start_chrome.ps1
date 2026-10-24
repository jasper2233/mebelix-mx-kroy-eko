# Onlayn tizim (GibLab online) uchun ALOHIDA Chrome nusxasi: o'z profili + boshqaruv porti 9222 (MCP `GIBLAB_MODE=cdp` va
# tools/giblab/gl.mjs shunga ulanadi). Foydalanuvchining oddiy Chrome'iga tegmaydi. Qotib qolsa: -Restart (shu nusxani yopib qayta ochadi).
# Birinchi marta foydalanuvchi o'zi kiradi («Оставаться в системе»); parol hech qayerda saqlanmaydi va skriptga berilmaydi.
param([switch]$Restart)
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profile = Join-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot))) "giblab-chrome-profile"
$port = 9222
if ($Restart) {
  Get-CimInstance Win32_Process -Filter "name='chrome.exe'" | Where-Object { $_.CommandLine -like "*$profile*" } |
    ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }
  Start-Sleep -Seconds 2
}
$running = Get-CimInstance Win32_Process -Filter "name='chrome.exe'" | Where-Object { $_.CommandLine -like "*$profile*" }
if (-not $running) {
  Start-Process -FilePath $chrome -ArgumentList "--remote-debugging-port=$port", "--user-data-dir=`"$profile`"", "--no-first-run",
    "--no-default-browser-check", "--window-size=1920,1040", "https://giblab.com/#projects"
}
"profile: $profile ; port: $port"
