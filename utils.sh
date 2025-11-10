#!/bin/bash
# Utilitários para Custom Knowledge Base
# Script genérico compatível com Linux/Mac/Windows (Git Bash/WSL)

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função de ajuda
show_help() {
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}    Utilitários - Custom Knowledge Base${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Uso:${NC} ./utils.sh <comando> [opções]"
    echo ""
    echo -e "${GREEN}Comandos Disponíveis:${NC}"
    echo ""
    echo -e "  ${BLUE}restart${NC}              Reiniciar containers Docker"
    echo -e "  ${BLUE}logs${NC}                 Ver logs da aplicação"
    echo -e "  ${BLUE}status${NC}               Status dos containers e sistema"
    echo -e "  ${BLUE}test${NC} <query>         Testar query com timing"
    echo -e "  ${BLUE}add-article${NC} <title>  Adicionar artigo da Wikipedia"
    echo -e "  ${BLUE}search${NC} <query>       Busca semântica"
    echo -e "  ${BLUE}shell${NC}                Abrir shell no container"
    echo -e "  ${BLUE}qdrant-info${NC}          Informações do Qdrant"
    echo -e "  ${BLUE}python${NC} <script>      Executar script Python no container"
    echo ""
    echo -e "${YELLOW}Exemplos:${NC}"
    echo -e "  ./utils.sh restart"
    echo -e "  ./utils.sh test \"Quem foi o primeiro imperador inca?\""
    echo -e "  ./utils.sh add-article \"Machu Picchu\""
    echo -e "  ./utils.sh search \"Cusco\""
    echo -e "  ./utils.sh python scripts/listar_artigos.py"
    echo ""
}

# Função para reiniciar containers
restart_containers() {
    echo -e "${YELLOW}🔄 Reiniciando containers...${NC}"
    docker-compose down
    echo -e "${BLUE}🔨 Reconstruindo imagens...${NC}"
    docker-compose build
    echo -e "${GREEN}🚀 Iniciando containers...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ Containers reiniciados!${NC}"
    echo ""
    docker-compose ps
}

# Função para ver logs
view_logs() {
    echo -e "${CYAN}📋 Logs da aplicação (Ctrl+C para sair):${NC}"
    docker-compose logs -f offline_wikipedia_app
}

# Função para status
show_status() {
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}    Status do Sistema${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}🐳 Containers Docker:${NC}"
    docker-compose ps
    echo ""
    echo -e "${YELLOW}📊 Uso de recursos:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" || true
    echo ""
    echo -e "${YELLOW}🔍 Informações do Qdrant:${NC}"
    curl -s http://localhost:6333/collections/wikipedia_langchain 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Qdrant não disponível ou coleção não encontrada"
}

# Função para testar query
test_query() {
    local query="$1"
    if [ -z "$query" ]; then
        echo -e "${RED}❌ Erro: Query não fornecida${NC}"
        echo -e "Uso: ./utils.sh test \"sua pergunta aqui\""
        exit 1
    fi
    
    echo -e "${CYAN}🔍 Testando query: ${YELLOW}$query${NC}"
    echo -e "${BLUE}⏱️  Medindo tempo de resposta...${NC}"
    echo ""
    
    curl -X POST http://localhost:5002/perguntar \
        -H "Content-Type: application/json" \
        -d "{\"pergunta\": \"$query\"}" \
        -w "\n\n⏱️  Tempo total: %{time_total}s\n" \
        2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Erro ao executar query"
}

# Função para adicionar artigo
add_article() {
    local title="$1"
    if [ -z "$title" ]; then
        echo -e "${RED}❌ Erro: Título não fornecido${NC}"
        echo -e "Uso: ./utils.sh add-article \"Título do Artigo\""
        exit 1
    fi
    
    echo -e "${CYAN}📥 Adicionando artigo: ${YELLOW}$title${NC}"
    echo ""
    
    curl -X POST http://localhost:5002/adicionar-artigo \
        -H "Content-Type: application/json" \
        -d "{\"titulo\": \"$title\", \"reprocessar\": false}" \
        2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Erro ao adicionar artigo"
}

# Função para busca semântica
semantic_search() {
    local query="$1"
    if [ -z "$query" ]; then
        echo -e "${RED}❌ Erro: Query não fornecida${NC}"
        echo -e "Uso: ./utils.sh search \"termo de busca\""
        exit 1
    fi
    
    echo -e "${CYAN}🔎 Busca semântica: ${YELLOW}$query${NC}"
    echo ""
    
    curl -X POST http://localhost:5002/buscar \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\", \"limit\": 5}" \
        2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Erro ao buscar"
}

# Função para abrir shell no container
open_shell() {
    echo -e "${CYAN}🐚 Abrindo shell no container...${NC}"
    echo -e "${YELLOW}Digite 'exit' para sair${NC}"
    echo ""
    docker-compose exec offline_wikipedia_app /bin/bash
}

# Função para informações do Qdrant
qdrant_info() {
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}    Informações do Qdrant${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}📊 Coleções:${NC}"
    curl -s http://localhost:6333/collections 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Erro ao obter coleções"
    echo ""
    echo -e "${YELLOW}📈 Detalhes da coleção wikipedia_langchain:${NC}"
    curl -s http://localhost:6333/collections/wikipedia_langchain 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Coleção não encontrada"
}

# Função para executar script Python
run_python() {
    local script="$1"
    if [ -z "$script" ]; then
        echo -e "${RED}❌ Erro: Script não fornecido${NC}"
        echo -e "Uso: ./utils.sh python <caminho/do/script.py>"
        exit 1
    fi
    
    if [ ! -f "$script" ]; then
        echo -e "${RED}❌ Erro: Arquivo não encontrado: $script${NC}"
        exit 1
    fi
    
    local script_name=$(basename "$script")
    local script_dir=$(dirname "$script")
    
    echo -e "${CYAN}🐍 Executando: ${YELLOW}$script${NC}"
    echo ""
    
    docker-compose exec offline_wikipedia_app python "/app/$script"
}

# Main
case "${1:-}" in
    restart)
        restart_containers
        ;;
    logs)
        view_logs
        ;;
    status)
        show_status
        ;;
    test)
        test_query "$2"
        ;;
    add-article)
        add_article "$2"
        ;;
    search)
        semantic_search "$2"
        ;;
    shell)
        open_shell
        ;;
    qdrant-info)
        qdrant_info
        ;;
    python)
        run_python "$2"
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Comando desconhecido: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
