# Script para reiniciar Docker e resolver problemas de I/O
Write-Host "🔄 Reiniciando Docker Desktop..." -ForegroundColor Yellow

# Parar Docker Desktop
Write-Host "⏹️ Parando Docker Desktop..." -ForegroundColor Red
Get-Process -Name "*docker*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 10

# Limpar cache WSL se necessário
Write-Host "🧹 Limpando cache WSL..." -ForegroundColor Blue
wsl --shutdown

# Iniciar Docker Desktop
Write-Host "▶️ Iniciando Docker Desktop..." -ForegroundColor Green
Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden

# Aguardar inicialização
Write-Host "⏳ Aguardando Docker inicializar..." -ForegroundColor Yellow
$timeout = 120
$count = 0

do {
    Start-Sleep -Seconds 5
    $count += 5
    $status = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker iniciado com sucesso!" -ForegroundColor Green
        break
    }
    Write-Host "⏳ Aguardando... ($count/$timeout segundos)" -ForegroundColor Yellow
} while ($count -lt $timeout)

if ($count -ge $timeout) {
    Write-Host "❌ Timeout - Docker não iniciou corretamente" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Docker pronto para uso!" -ForegroundColor Green