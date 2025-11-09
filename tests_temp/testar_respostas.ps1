Write-Host "`n=== TESTES DO SISTEMA RAG ===" -ForegroundColor Cyan

# Teste 1: Krabi (deve retornar artigo)
Write-Host "`n[TESTE 1] Pergunta: 'o que é krabi?' (deve retornar artigo sobre Krabi)" -ForegroundColor Yellow
$body1 = @{ pergunta = "o que é krabi?" } | ConvertTo-Json
try {
    $resp1 = Invoke-WebRequest -Uri "http://localhost:9000/perguntar" -Method POST -ContentType "application/json; charset=utf-8" -Body $body1 -UseBasicParsing
    $json1 = $resp1.Content | ConvertFrom-Json
    $preview1 = $json1.resposta.Substring(0, [Math]::Min(120, $json1.resposta.Length))
    Write-Host "  Resposta: $preview1..." -ForegroundColor White
    Write-Host "  Fontes: $($json1.fontes.title -join ', ')" -ForegroundColor White
    if($json1.fontes.Count -gt 0 -and $json1.fontes.title -contains "Krabi") {
        Write-Host "  Status: ✅ PASSOU" -ForegroundColor Green
    } else {
        Write-Host "  Status: ❌ FALHOU (esperava ter Krabi nas fontes)" -ForegroundColor Red
    }
} catch {
    Write-Host "  Status: ❌ ERRO: $_" -ForegroundColor Red
}

# Teste 2: Praia da Joaquina (NÃO deve ter artigo)
Write-Host "`n[TESTE 2] Pergunta: 'o que é praia da joaquina?' (NÃO deve ter artigo)" -ForegroundColor Yellow
$body2 = @{ pergunta = "o que é praia da joaquina?" } | ConvertTo-Json
try {
    $resp2 = Invoke-WebRequest -Uri "http://localhost:9000/perguntar" -Method POST -ContentType "application/json; charset=utf-8" -Body $body2 -UseBasicParsing
    $json2 = $resp2.Content | ConvertFrom-Json
    Write-Host "  Resposta: $($json2.resposta)" -ForegroundColor White
    Write-Host "  Fontes: $($json2.fontes.Count)" -ForegroundColor White
    if($json2.resposta -like "*Ainda não existem artigos*") {
        Write-Host "  Status: ✅ PASSOU" -ForegroundColor Green
    } else {
        Write-Host "  Status: ❌ FALHOU (esperava mensagem padrão)" -ForegroundColor Red
    }
} catch {
    Write-Host "  Status: ❌ ERRO: $_" -ForegroundColor Red
}

# Teste 3: Porrete (deve retornar artigo)
Write-Host "`n[TESTE 3] Pergunta: 'o que é porrete?' (deve retornar artigo sobre Porrete)" -ForegroundColor Yellow
$body3 = @{ pergunta = "o que é porrete?" } | ConvertTo-Json
try {
    $resp3 = Invoke-WebRequest -Uri "http://localhost:9000/perguntar" -Method POST -ContentType "application/json; charset=utf-8" -Body $body3 -UseBasicParsing
    $json3 = $resp3.Content | ConvertFrom-Json
    $preview3 = $json3.resposta.Substring(0, [Math]::Min(120, $json3.resposta.Length))
    Write-Host "  Resposta: $preview3..." -ForegroundColor White
    Write-Host "  Fontes: $($json3.fontes.title -join ', ')" -ForegroundColor White
    if($json3.fontes.Count -gt 0 -and $json3.fontes.title -contains "Porrete") {
        Write-Host "  Status: ✅ PASSOU" -ForegroundColor Green
    } else {
        Write-Host "  Status: ❌ FALHOU (esperava ter Porrete nas fontes)" -ForegroundColor Red
    }
} catch {
    Write-Host "  Status: ❌ ERRO: $_" -ForegroundColor Red
}

# Teste 4: Bacamarte (NÃO deve ter artigo - não existe)
Write-Host "`n[TESTE 4] Pergunta: 'o que é bacamarte?' (NÃO deve ter artigo)" -ForegroundColor Yellow
$body4 = @{ pergunta = "o que é bacamarte?" } | ConvertTo-Json
try {
    $resp4 = Invoke-WebRequest -Uri "http://localhost:9000/perguntar" -Method POST -ContentType "application/json; charset=utf-8" -Body $body4 -UseBasicParsing
    $json4 = $resp4.Content | ConvertFrom-Json
    Write-Host "  Resposta: $($json4.resposta)" -ForegroundColor White
    Write-Host "  Fontes: $($json4.fontes.Count)" -ForegroundColor White
    if($json4.resposta -like "*Ainda não existem artigos*") {
        Write-Host "  Status: ✅ PASSOU" -ForegroundColor Green
    } else {
        Write-Host "  Status: ❌ FALHOU (esperava mensagem padrão)" -ForegroundColor Red
    }
} catch {
    Write-Host "  Status: ❌ ERRO: $_" -ForegroundColor Red
}

Write-Host "`n=== FIM DOS TESTES ===" -ForegroundColor Cyan
