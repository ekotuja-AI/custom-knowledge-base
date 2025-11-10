# Utilitários do Custom Knowledge Base
# Script com comandos úteis para gerenciar o sistema

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('restart', 'logs', 'status', 'test', 'add-article', 'search')]
    [string]$Command,
    
    [Parameter(Mandatory=$false)]
    [string]$Query,
    
    [Parameter(Mandatory=$false)]
    [string]$Title
)

function Show-Usage {
    Write-Host "`n📚 Custom Knowledge Base - Utilitários" -ForegroundColor Cyan
    Write-Host "=" * 60
    Write-Host "`nUso: .\utils.ps1 -Command <comando> [opções]`n"
    Write-Host "Comandos disponíveis:" -ForegroundColor Yellow
    Write-Host "  restart       - Reinicia os containers Docker"
    Write-Host "  logs          - Mostra logs da aplicação"
    Write-Host "  status        - Verifica status do sistema"
    Write-Host "  test          - Testa uma busca (requer -Query)"
    Write-Host "  add-article   - Adiciona artigo (requer -Title)"
    Write-Host "  search        - Busca semântica (requer -Query)"
    Write-Host "`nExemplos:" -ForegroundColor Yellow
    Write-Host "  .\utils.ps1 -Command restart"
    Write-Host "  .\utils.ps1 -Command test -Query 'o que é Python?'"
    Write-Host "  .\utils.ps1 -Command add-article -Title 'Python'"
    Write-Host "  .\utils.ps1 -Command search -Query 'programação'"
}

function Restart-Containers {
    Write-Host "`n🔄 Reiniciando containers..." -ForegroundColor Cyan
    docker-compose down
    docker-compose up -d
    Start-Sleep -Seconds 10
    Write-Host "✅ Containers reiniciados!" -ForegroundColor Green
    Get-Logs
}

function Get-Logs {
    Write-Host "`n📋 Últimos logs da aplicação:" -ForegroundColor Cyan
    docker logs --tail=30 offline_wikipedia_app
}

function Get-Status {
    Write-Host "`n📊 Status do Sistema:" -ForegroundColor Cyan
    Write-Host "=" * 60
    
    Write-Host "`n🐳 Containers:" -ForegroundColor Yellow
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host "`n🌐 Testando API..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9000/status" -Method GET
        Write-Host "✅ API Online" -ForegroundColor Green
        $response | ConvertTo-Json
    } catch {
        Write-Host "❌ API Offline" -ForegroundColor Red
    }
}

function Test-Query {
    param([string]$QueryText)
    
    if (-not $QueryText) {
        Write-Host "❌ Erro: Query não fornecida. Use -Query 'sua pergunta'" -ForegroundColor Red
        return
    }
    
    Write-Host "`n🔍 Testando pergunta: '$QueryText'" -ForegroundColor Cyan
    
    $body = @{
        pergunta = $QueryText
        max_chunks = 3
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9000/perguntar" -Method POST -Body $body -ContentType "application/json"
        
        Write-Host "`n📝 Resposta:" -ForegroundColor Green
        Write-Host $response.resposta
        
        Write-Host "`n⏱️ Timing:" -ForegroundColor Yellow
        if ($response.model_info.timing) {
            $timing = $response.model_info.timing
            Write-Host "  Busca: $($timing.search_time)s"
            Write-Host "  Geração: $($timing.generation_time)s"
            Write-Host "  Total: $($timing.total_time)s"
        }
        
        Write-Host "`n📄 Documentos: $($response.documentos_encontrados.Count)" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ Erro ao executar query: $_" -ForegroundColor Red
    }
}

function Add-Article {
    param([string]$ArticleTitle)
    
    if (-not $ArticleTitle) {
        Write-Host "❌ Erro: Título não fornecido. Use -Title 'Nome do Artigo'" -ForegroundColor Red
        return
    }
    
    Write-Host "`n➕ Adicionando artigo: '$ArticleTitle'" -ForegroundColor Cyan
    
    $body = @{
        titulo = $ArticleTitle
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9000/adicionar" -Method POST -Body $body -ContentType "application/json"
        
        Write-Host "✅ Artigo adicionado com sucesso!" -ForegroundColor Green
        Write-Host "  Título: $($response.titulo)"
        Write-Host "  URL: $($response.url)"
        Write-Host "  Chunks: $($response.chunks_adicionados)"
    } catch {
        Write-Host "❌ Erro ao adicionar artigo: $_" -ForegroundColor Red
    }
}

function Search-Semantic {
    param([string]$SearchQuery)
    
    if (-not $SearchQuery) {
        Write-Host "❌ Erro: Query não fornecida. Use -Query 'termo de busca'" -ForegroundColor Red
        return
    }
    
    Write-Host "`n🔍 Buscando: '$SearchQuery'" -ForegroundColor Cyan
    
    $body = @{
        query = $SearchQuery
        limit = 5
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9000/buscar" -Method POST -Body $body -ContentType "application/json"
        
        Write-Host "`n📊 Resultados encontrados: $($response.total_resultados)" -ForegroundColor Green
        
        foreach ($resultado in $response.resultados) {
            Write-Host "`n📄 $($resultado.title) (score: $([math]::Round($resultado.score, 4)))" -ForegroundColor Yellow
            $preview = $resultado.content.Substring(0, [Math]::Min(150, $resultado.content.Length))
            Write-Host "   $preview..."
        }
    } catch {
        Write-Host "❌ Erro ao executar busca: $_" -ForegroundColor Red
    }
}

# Main
if (-not $Command) {
    Show-Usage
    exit
}

switch ($Command) {
    'restart' { Restart-Containers }
    'logs' { Get-Logs }
    'status' { Get-Status }
    'test' { Test-Query -QueryText $Query }
    'add-article' { Add-Article -ArticleTitle $Title }
    'search' { Search-Semantic -SearchQuery $Query }
}
