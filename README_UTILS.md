# 🛠️ Utilitários - Custom Knowledge Base

Scripts utilitários para gerenciar o projeto de forma genérica e multiplataforma.

## 📁 Arquivos

### `utils.sh` (Linux/Mac/Git Bash/WSL)
Script shell genérico compatível com sistemas Unix-like.

**Uso no Linux/Mac:**
```bash
chmod +x utils.sh
./utils.sh <comando> [opções]
```

**Uso no Windows (Git Bash/WSL):**
```bash
bash utils.sh <comando> [opções]
```

### `utils.ps1` (Windows PowerShell)
Script PowerShell para usuários Windows nativos (mantido por compatibilidade).

**Uso:**
```powershell
.\utils.ps1 -Command <comando> [-Query "texto"] [-Title "título"]
```

## 🎯 Comandos Disponíveis

Ambos os scripts suportam os mesmos comandos:

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `restart` | Reiniciar containers Docker | `./utils.sh restart` |
| `logs` | Ver logs da aplicação | `./utils.sh logs` |
| `status` | Status dos containers e sistema | `./utils.sh status` |
| `test` | Testar query com timing | `./utils.sh test "Quem foi o primeiro imperador inca?"` |
| `add-article` | Adicionar artigo da Wikipedia | `./utils.sh add-article "Machu Picchu"` |
| `search` | Busca semântica | `./utils.sh search "Cusco"` |
| `shell` | Abrir shell no container | `./utils.sh shell` |
| `qdrant-info` | Informações do Qdrant | `./utils.sh qdrant-info` |
| `python` | Executar script Python | `./utils.sh python scripts/listar_artigos.py` |

## 🌍 Multiplataforma

### Linux/Mac
```bash
chmod +x utils.sh
./utils.sh status
./utils.sh test "sua pergunta"
```

### Windows (Git Bash)
```bash
bash utils.sh status
bash utils.sh test "sua pergunta"
```

### Windows (WSL)
```bash
./utils.sh status
./utils.sh test "sua pergunta"
```

### Windows (PowerShell Nativo)
```powershell
.\utils.ps1 -Command status
.\utils.ps1 -Command test -Query "sua pergunta"
```

## 🐳 Comandos Docker

Todos os comandos são executados usando `docker-compose`, funcionando de forma idêntica em qualquer plataforma:

- ✅ Linux
- ✅ macOS
- ✅ Windows (Docker Desktop)
- ✅ WSL2

## 📊 Exemplos de Uso

### Reiniciar o Sistema
```bash
./utils.sh restart
```

### Verificar Status
```bash
./utils.sh status
```

### Testar uma Query
```bash
./utils.sh test "Qual foi a capital do Império Inca?"
```

### Adicionar um Artigo
```bash
./utils.sh add-article "Pachacútec"
```

### Buscar Semanticamente
```bash
./utils.sh search "civilização andina"
```

### Abrir Shell Interativo
```bash
./utils.sh shell
# Dentro do container:
python scripts/listar_artigos.py
exit
```

### Executar Script Python
```bash
./utils.sh python scripts/listar_artigos.py
```

### Ver Informações do Qdrant
```bash
./utils.sh qdrant-info
```

## 🔧 Requisitos

### Para `utils.sh`:
- Docker e Docker Compose
- Bash (incluído no Git Bash para Windows)
- curl (para chamadas API)
- python3 (para formatação JSON - opcional)

### Para `utils.ps1`:
- Docker e Docker Compose
- PowerShell 5.1+ (incluído no Windows)

## 💡 Dicas

1. **Use `utils.sh` para máxima compatibilidade** - funciona em todos os sistemas
2. **Use `utils.ps1` apenas se você preferir PowerShell** no Windows
3. **Adicione ao PATH** para executar de qualquer lugar:
   ```bash
   # Linux/Mac - adicione ao ~/.bashrc ou ~/.zshrc
   alias dvutils='cd /caminho/para/projeto && ./utils.sh'
   ```

## 🚀 Integração CI/CD

O `utils.sh` pode ser usado em pipelines CI/CD:

```yaml
# GitHub Actions
- name: Test API
  run: |
    bash utils.sh status
    bash utils.sh test "test query"

# GitLab CI
script:
  - bash utils.sh restart
  - bash utils.sh status
```

## 📝 Notas

- Scripts **não modificam código** - apenas gerenciam containers e API
- Comandos são **idempotentes** - podem ser executados múltiplas vezes
- Logs são **formatados com cores** para melhor legibilidade
- **Tratamento de erros** em todas as operações
