# Testes Unitários - Custom Knowledge Base

Esta pasta contém os testes unitários e de integração leves para o projeto.

## 📋 Estrutura de Testes

```
tests/
├── __init__.py                 # Inicialização do pacote de testes
├── test_models.py              # Testes dos modelos Pydantic
├── test_services.py            # Testes dos serviços (métodos rápidos)
├── test_config.py              # Testes de configuração
└── test_integration.py         # Testes de integração leves
```

## 🚀 Como Executar os Testes

### Executar todos os testes
```bash
pytest
```

### Executar testes de um arquivo específico
```bash
pytest tests/test_models.py
```

### Executar um teste específico
```bash
pytest tests/test_models.py::TestSearchResult::test_criar_search_result_minimo
```

### Executar com mais detalhes (verbose)
```bash
pytest -v
```

### Executar apenas testes unitários (marcados como @pytest.mark.unit)
```bash
pytest -m unit
```

### Ver cobertura de código
```bash
pytest --cov=api --cov=services --cov-report=html
```

## 📊 Categorias de Testes

### ✅ Testes Incluídos (Rápidos)

- **test_models.py**: 
  - Criação e validação de modelos Pydantic
  - Validação de campos obrigatórios
  - Testes de tipos de dados

- **test_services.py**:
  - Divisão de texto em chunks
  - Inicialização de serviços
  - Processamento de resultados
  - Obtenção de estatísticas

- **test_config.py**:
  - Configurações da aplicação
  - Variáveis de ambiente
  - Valores padrão

- **test_integration.py**:
  - Criação de objetos complexos
  - Fluxos básicos sem I/O
  - Validação de estruturas

### ❌ Testes Excluídos (Lentos/Complexos)

Os seguintes testes **NÃO** foram incluídos por serem lentos ou complexos:

- ❌ Processamento de documentos completos da Wikipedia
- ❌ Geração de embeddings reais (SentenceTransformer)
- ❌ Chamadas reais à API do Ollama
- ❌ Inserção/busca no Qdrant
- ❌ Download de modelos de ML
- ❌ Processamento de dumps do Wikipedia
- ❌ Testes end-to-end com FastAPI

## 🎯 Cobertura

Os testes focam em:
- ✅ Lógica de negócio sem I/O
- ✅ Validação de modelos
- ✅ Processamento de texto simples
- ✅ Configurações e defaults
- ✅ Criação de objetos
- ✅ Métodos auxiliares

## 🆕 Cobertura Multi-Coleção/Modelo
- Testes cobrem operações com múltiplas coleções e troca dinâmica de modelo de embedding via API/script.

## 📦 Dependências de Teste

Para executar os testes, instale:

```bash
pip install pytest pytest-cov
```

## 🔍 Exemplos de Uso

### Teste específico com output detalhado
```bash
pytest tests/test_models.py::TestSearchResult -v -s
```

### Teste com breakpoint para debug
```bash
pytest tests/test_services.py --pdb
```

### Gerar relatório HTML de cobertura
```bash
pytest --cov=. --cov-report=html
# Abra htmlcov/index.html no navegador
```

## 📝 Notas

- Todos os testes devem executar em **menos de 5 segundos** total
- Testes não requerem serviços externos (Docker, Qdrant, Ollama)
- Mocks são usados quando necessário para evitar I/O
- Testes são independentes e podem rodar em qualquer ordem
