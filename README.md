# 📖 Sistema Wikipedia Offline# Wikipedia Semantic Search API 🔍



Sistema completo de consulta offline da Wikipedia em português utilizando tecnologias modernas de IA e processamento vetorial.**API REST para busca semântica em artigos da Wikipedia com sistema RAG integrado usando LangChain e LLM.**



## ⚡ Características Principais[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/downloads/)

- 🌐 **100% Offline**: Funciona sem conexão com a internet[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

- 🤖 **IA Integrada**: Respostas inteligentes usando Ollama (phi3:mini)[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

- 🔍 **Busca Vetorial**: Pesquisa semântica usando Qdrant

- 📚 **Wikipedia Real**: Processa dumps oficiais da Wikipedia em português## 🎯 Visão Geral

- 🐳 **Docker**: Deploy simplificado com containers

- ⚡ **Performance**: Processamento otimizado de grandes volumes de dadosUma API moderna que combina **busca semântica** com **inteligência artificial** para explorar o conhecimento da Wikipedia de forma inteligente. Utilizando **embeddings**, **LangChain** e **LLM**, oferece tanto busca tradicional quanto respostas contextualizadas para perguntas complexas.



## 🏗️ Arquitetura### ✨ Funcionalidades Principais



```🔍 **Busca Semântica Avançada**

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐- Busca por conceitos, não apenas palavras-chave

│   FastAPI       │    │    Qdrant       │    │    Ollama       │- Encontra artigos relacionados semanticamente

│   (Port 9000)   │◄──►│   (Port 6333)   │    │  (Port 11434)   │- Resultados ordenados por relevância

│                 │    │                 │    │                 │

│ • Wikipedia API │    │ • Vector DB     │    │ • LLM Local     │🤖 **Sistema RAG (Retrieval-Augmented Generation)**

│ • Dump Parser   │    │ • 384 dims      │    │ • phi3:mini     │- Respostas inteligentes para perguntas complexas

│ • Status/Stats  │    │ • Cosine dist   │    │ • 2.2GB model   │- LLM integrado com conhecimento da Wikipedia

└─────────────────┘    └─────────────────┘    └─────────────────┘- Citação automática das fontes utilizadas

```

📚 **Base de Conhecimento Dinâmica**

## 🚀 Início Rápido- Artigos da Wikipedia em português

- Adição dinâmica de novos artigos

### Pré-requisitos- Processamento automático com LangChain

- Docker e Docker Compose

- 8GB+ RAM disponível🚀 **API REST Moderna**

- 15GB+ espaço em disco- Documentação interativa automática

- Validação automática de dados

### 1. Clone e Execute- Endpoints intuitivos e bem documentados

```bash

git clone <repo-url>## 🏗️ Arquitetura

cd dicionario_vetorial

docker-compose up -d```

```┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐

│   FastAPI       │    │  LangChain   │    │    Qdrant      │

### 2. Aguarde a Inicialização│   (REST API)    │◄──►│ (Processing) │◄──►│ (Vector Store)  │

O sistema irá:└─────────────────┘    └──────────────┘    └─────────────────┘

- ✅ Inicializar Qdrant (banco vetorial)         │                       │                    │

- ✅ Baixar Ollama phi3:mini (2.2GB)         ▼                       ▼                    ▼

- ✅ Configurar FastAPI┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐

│   OpenAI GPT    │    │  Wikipedia   │    │ SentenceTransf. │

### 3. Acesse a API│     (LLM)       │    │    (API)     │    │  (Embeddings)   │

- **Interface Web**: http://localhost:9000/docs└─────────────────┘    └──────────────┘    └─────────────────┘

- **Status do Sistema**: http://localhost:9000/status```

- **Estatísticas**: http://localhost:9000/estatisticas

### 🛠️ Stack Tecnológico

## 📊 Endpoints Principais

- **[FastAPI](https://fastapi.tiangolo.com/)**: Framework web assíncrono de alta performance

### Sistema- **[Qdrant](https://qdrant.tech/)**: Banco de dados vetorial especializado

- `GET /status` - Status geral do sistema- **[LangChain](https://python.langchain.com/)**: Framework para aplicações com LLM

- `GET /estatisticas` - Métricas da base de dados- **[SentenceTransformers](https://www.sbert.net/)**: Modelos de embedding multilíngues

- `GET /health` - Health check- **[OpenAI GPT](https://openai.com/)**: Large Language Model para respostas inteligentes

- **[Wikipedia API](https://pypi.org/project/wikipedia/)**: Acesso aos artigos da Wikipedia

### Consultas- **[Docker](https://www.docker.com/)**: Containerização para deployment fácil

- `POST /pesquisar` - Busca semântica na Wikipedia

- `POST /responder` - Pergunta com IA (contexto + LLM)## 🚀 Quick Start



### Dados Wikipedia### Pré-requisitos

- `POST /dumps/download` - Download de dumps oficiais

- `POST /dumps/processar-real` - Processa dumps baixados- **Docker & Docker Compose** (recomendado)

- `POST /dumps/descomprimir-e-processar` - Método otimizado para BZ2- Ou **Python 3.11+** para execução local

- `GET /dumps/status-download` - Progresso dos downloads- **Chave da API OpenAI** (opcional, para funcionalidade RAG)



### Expansão de Dados### 1. Clone o Repositório

- `POST /wikipedia-api/expandir-base` - Adiciona artigos via API

```bash

## 🔧 Configuraçãogit clone https://github.com/ekotuja-AI/dicionario_vetorial.git

cd dicionario_vetorial

### Variáveis de Ambiente (.env)```

```env

# Qdrant### 2. Configuração (Opcional)

QDRANT_HOST=qdrant

QDRANT_PORT=6333Para usar o sistema RAG com LLM, configure sua chave da OpenAI:



# Ollama```bash

OLLAMA_HOST=ollama# Copie o arquivo de exemplo

OLLAMA_PORT=11434cp .env.example .env

LLM_MODEL=phi3:mini

# Edite .env e adicione sua chave

# EmbeddingsOPENAI_API_KEY=your_openai_api_key_here

EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2```



# Dados### 3. Inicie com Docker (Recomendado)

DATA_DIR=/app/data

``````bash

# Inicia todos os serviços automaticamente

### Volumes Persistentesdocker-compose up --build

- `qdrant_storage`: Dados do banco vetorial

- `ollama_models`: Modelos de IA baixados# Para executar em background

- `./data`: Dumps XML e cachedocker-compose up --build -d

```

## 📈 Dados Atuais

### 4. Acesse a API

O sistema já possui:

- **93 chunks** de artigos da WikipediaA API estará disponível em:

- **384 dimensões** por vetor- **API**: http://localhost:9000

- **Distância Cosine** para similaridade- **Documentação Swagger**: http://localhost:9000/docs

- **Processamento BZ2** para dumps oficiais- **Documentação ReDoc**: http://localhost:9000/redoc



## 🛠️ Comandos Úteis## 📖 Uso da API



### Download e Processamento### 🔍 Busca Semântica

```bash

# Baixar dumps da Wikipedia PTEncontre artigos relacionados a um conceito:

curl -X POST "http://localhost:9000/dumps/download?dump_type=pages-articles"

```bash

# Processar dump baixado (método otimizado)curl -X POST "http://localhost:9000/buscar" \

curl -X POST "http://localhost:9000/dumps/descomprimir-e-processar?filename=ptwiki-20251020-pages-articles.xml.bz2&max_artigos=1000"  -H "Content-Type: application/json" \

  -d '{

# Expandir base via API Wikipedia    "query": "inteligência artificial e machine learning",

curl -X POST "http://localhost:9000/wikipedia-api/expandir-base?num_artigos=100"    "limit": 5

```  }'

```

### Consultas

```bash**Resposta:**

# Busca semântica```json

curl -X POST "http://localhost:9000/pesquisar" \{

  -H "Content-Type: application/json" \  "query": "inteligência artificial e machine learning",

  -d '{"query": "inteligência artificial", "limit": 5}'  "total_resultados": 5,

  "resultados": [

# Pergunta com IA    {

curl -X POST "http://localhost:9000/responder" \      "title": "Inteligência artificial",

  -H "Content-Type: application/json" \      "content": "Inteligência artificial é a simulação de processos...",

  -d '{"pergunta": "O que é machine learning?"}'      "url": "https://pt.wikipedia.org/wiki/Intelig%C3%AAncia_artificial",

```      "score": 0.9234

    }

### Monitoramento  ],

```bash  "tempo_busca_ms": 45.2

# Status dos containers}

docker-compose ps```



# Logs da aplicação### 🤖 Perguntas com RAG

docker-compose logs -f app

Faça perguntas complexas e obtenha respostas contextualizadas:

# Estatísticas do sistema

curl http://localhost:9000/estatisticas```bash

```curl -X POST "http://localhost:9000/perguntar" \

  -H "Content-Type: application/json" \

## 📁 Estrutura do Projeto  -d '{

    "pergunta": "O que é inteligência artificial e como ela funciona?",

```    "max_chunks": 5

dicionario_vetorial/  }'

├── docker-compose.yml           # Orquestração```

├── Dockerfile                   # Imagem da app

├── requirements_minimal.txt     # Dependencies**Resposta:**

├── .env / .env.example         # Configurações```json

├── data/                       # Dumps e cache{

├── api/  "pergunta": "O que é inteligência artificial e como ela funciona?",

│   ├── wikipediaFuncionalAPI.py # API principal  "resposta": "Inteligência artificial (IA) é um campo da ciência da computação que visa criar sistemas capazes de realizar tarefas que normalmente requerem inteligência humana...",

│   ├── config.py               # Configurações  "fontes": [

│   └── models.py               # Modelos Pydantic    {

└── services/      "title": "Inteligência artificial",

    ├── wikipediaOfflineService.py  # Integração Qdrant      "content": "Conteúdo relevante...",

    ├── wikipediaDumpService.py     # Parser XML      "url": "https://pt.wikipedia.org/wiki/Intelig%C3%AAncia_artificial",

    └── offlineWikipediaService.py  # Serviços base      "score": 0.9234

```    }

  ],

## 🔍 Funcionalidades Avançadas  "raciocinio": "Resposta gerada baseada em 3 fontes relevantes da Wikipedia.",

  "tempo_processamento_ms": 1250.5

### Processamento de Dumps}

- ✅ **BZ2/GZ Support**: Descompressão automática```

- ✅ **Chunking Inteligente**: Divisão otimizada de artigos

- ✅ **Namespace Filtering**: Apenas artigos principais### 📚 Adicionar Conteúdo

- ✅ **Progress Monitoring**: Acompanhamento em tempo real

Adicione novos artigos da Wikipedia à base:

### Busca Vetorial

- ✅ **Embeddings Multilíngues**: Modelo otimizado para português```bash

- ✅ **Similaridade Semântica**: Busca por contexto, não apenas palavrascurl -X POST "http://localhost:9000/adicionar" \

- ✅ **Ranking por Relevância**: Resultados ordenados por similaridade  -H "Content-Type: application/json" \

  -d '{

### IA Conversacional    "titulo": "Ciência de dados"

- ✅ **LLM Local**: Processamento sem envio de dados externos  }'

- ✅ **Contexto Relevante**: Respostas baseadas em artigos similares```

- ✅ **Respostas Estruturadas**: Output formatado e organizado

## 📊 Endpoints Disponíveis

## 🚨 Solução de Problemas

| Endpoint | Método | Descrição |

### Container não inicia|----------|--------|-----------|

```bash| `/` | GET | Informações da API |

docker-compose down| `/status` | GET | Status dos componentes |

docker-compose build --no-cache| `/estatisticas` | GET | Estatísticas da base |

docker-compose up -d| `/buscar` | POST | Busca semântica |

```| `/perguntar` | POST | Perguntas com RAG |

| `/adicionar` | POST | Adicionar artigo |

### Ollama não baixa modelo| `/docs` | GET | Documentação Swagger |

```bash| `/redoc` | GET | Documentação ReDoc |

docker-compose exec ollama ollama pull phi3:mini

```## 🔧 Configuração Avançada



### Qdrant sem conexão### Variáveis de Ambiente

```bash

# Verificar se porta 6333 está livre```bash

netstat -an | findstr 6333# Qdrant

```QDRANT_HOST=localhost

QDRANT_PORT=6333

### Performance lenta

- Aumente memória disponível para Docker# OpenAI (para RAG)

- Verifique espaço em disco disponívelOPENAI_API_KEY=your_api_key_here

- Use SSD para melhor I/O

# Configurações do LLM

## 📊 Monitoramento de PerformanceLLM_MODEL=gpt-3.5-turbo

LLM_TEMPERATURE=0.3

### Métricas ImportantesLLM_MAX_TOKENS=1000

- **Chunks/segundo**: Velocidade de processamento

- **Tempo de resposta**: Latência das consultas# Processamento de texto

- **Uso de memória**: Ollama + Qdrant + AppCHUNK_SIZE=1000

- **Espaço em disco**: Dumps + modelos + índicesCHUNK_OVERLAP=200



### Logs Úteis# Busca

```bashDEFAULT_SEARCH_LIMIT=10

# Performance de processamentoMAX_SEARCH_LIMIT=50

docker-compose logs app | grep "chunks/segundo"```



# Erros de conexão### Execução Local (Desenvolvimento)

docker-compose logs app | grep "ERROR"

Se preferir executar sem Docker:

# Status de downloads

curl http://localhost:9000/dumps/status-download```bash

```# 1. Inicie apenas o Qdrant

docker run -p 6333:6333 qdrant/qdrant:v1.11.3

## 🎯 Próximos Passos

# 2. Instale dependências

1. **Expandir Base**: Processar dumps completos (10GB+)pip install -r requirements.txt

2. **Otimizar Queries**: Cache de resultados frequentes

3. **Interface Web**: Frontend para uso mais amigável# 3. Execute a API

4. **APIs Externas**: Integração com outras fontespython -m api.wikipediaAPI

5. **Backup/Restore**: Sistema de backup dos dados```



---## 📁 Estrutura do Projeto



**Desenvolvido com ❤️ usando FastAPI, Qdrant, Ollama e Docker**```
dicionario_vetorial/
├── 📁 api/                     # Camada da API REST
│   ├── wikipediaAPI.py         # Endpoints FastAPI
│   ├── models.py               # Modelos Pydantic
│   └── config.py               # Configurações
├── 📁 services/                # Lógica de negócio
│   └── wikipediaService.py     # Serviço principal
├── 🐳 docker-compose.yml       # Orquestração Docker
├── 🐳 Dockerfile              # Imagem da aplicação
├── 📋 requirements.txt         # Dependências Python
├── 🔧 .env.example            # Exemplo de configuração
└── 📖 README.md               # Esta documentação
```

## 🧪 Exemplos de Uso

### Casos de Uso Comuns

1. **Pesquisa Acadêmica**
   ```bash
   # Buscar artigos sobre um tópico
   "energia renovável e sustentabilidade"
   
   # Fazer pergunta específica
   "Quais são os principais tipos de energia renovável?"
   ```

2. **Exploração de Conceitos**
   ```bash
   # Buscar conceitos relacionados
   "blockchain e criptomoedas"
   
   # Entender relações
   "Como blockchain se relaciona com segurança digital?"
   ```

3. **Educação e Aprendizado**
   ```bash
   # Buscar material educativo
   "história da computação"
   
   # Obter explicações didáticas
   "Explique como funciona a internet de forma simples"
   ```

### Scripts de Teste

```python
import requests

# Teste de busca semântica
response = requests.post('http://localhost:9000/buscar', json={
    'query': 'inteligência artificial',
    'limit': 3
})
print(response.json())

# Teste de pergunta RAG
response = requests.post('http://localhost:9000/perguntar', json={
    'pergunta': 'O que é machine learning?',
    'max_chunks': 3
})
print(response.json())

# Adicionar novo artigo
response = requests.post('http://localhost:9000/adicionar', json={
    'titulo': 'Deep learning'
})
print(response.json())
```

## 🔧 Troubleshooting

### Problemas Comuns

**1. Qdrant não conecta**
```bash
# Verifique se o container está rodando
docker ps | grep qdrant

# Verifique os logs
docker logs qdrant
```

**2. LLM não funciona**
```bash
# Verifique se a chave da OpenAI está configurada
echo $OPENAI_API_KEY

# Teste a conectividade
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

**3. Modelo demora para carregar**
```bash
# O modelo SentenceTransformers é baixado na primeira execução
# Downloads subsequentes usam cache local em ~/.cache/
```

**4. Erro de memória**
```bash
# Se executando no Docker, aumente a memória disponível
# Ou use uma máquina com pelo menos 4GB RAM
```

### Logs e Monitoramento

```bash
# Logs da aplicação
docker logs wikipedia_search_app

# Logs do Qdrant
docker logs qdrant

# Logs em tempo real
docker-compose logs -f
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Desenvolvendo

```bash
# Clone e configure ambiente de desenvolvimento
git clone https://github.com/ekotuja-AI/dicionario_vetorial.git
cd dicionario_vetorial

# Instale dependências de desenvolvimento
pip install -r requirements.txt
pip install black isort pytest

# Execute testes
pytest

# Formate código
black .
isort .
```

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [Wikipedia](https://www.wikipedia.org/) pela base de conhecimento
- [LangChain](https://python.langchain.com/) pelo framework de processamento
- [Qdrant](https://qdrant.tech/) pelo banco de dados vetorial
- [FastAPI](https://fastapi.tiangolo.com/) pelo framework web
- [OpenAI](https://openai.com/) pelos modelos de linguagem

---

**Feito com ❤️ usando Python e tecnologias modernas de IA**