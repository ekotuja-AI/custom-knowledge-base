import logging

# Configurar logging com nivel DEBUG para ver todos os logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

"""
API Wikipedia Offline - Versão Funcional

API que integra Qdrant + Ollama + Wikipedia de forma funcional.
"""

import time
from contextlib import asynccontextmanager
from typing import List
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from services.wikipediaOfflineService import wikipedia_offline_service
from services.wikipediaDumpService import wikipedia_dump_processor
# Modelos Pydantic importados do utilitário
from .models import (
    BuscarRequest,
    WikipediaResultModel,
    BuscarResponse,
    PerguntarRequest,
    RAGResponseModel,
    BuscaPreviaResponse,
    AdicionarArtigoRequest,
    AdicionarArtigoResponse,
    StatusResponse,
    User,
    KnowledgeBase
)
from .telemetria_ws import router as telemetria_router

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Inicializando serviços...")
    wikipedia_offline_service.inicializar()
    logger.info("✅ Serviços inicializados!")
    yield
    # Shutdown
    logger.info("👋 Encerrando serviços...")

# Definição do objeto FastAPI
app = FastAPI(
    title="Wikipedia Offline Vector Search API - Funcional",
    lifespan=lifespan,
    description="API offline para Wikipedia com LLM local.\n\n### 🤖 RAG com LLM Local\n- Perguntas respondidas pelo modelo Phi-3 Mini\n- Respostas baseadas em artigos da Wikipedia\n- Sistema completamente offline\n\n### 📚 Gestão de Conteúdo\n- Adicione artigos da Wikipedia à base local\n- Processamento automático em chunks\n- Armazenamento no Qdrant\n\n## 🛠️ Stack Tecnológica\n- Qdrant: Banco vetorial para busca semântica\n- Ollama + Phi-3: LLM local para respostas\n- FastAPI: API REST moderna\n- Wikipedia API: Fonte de dados\n\n## 🚀 Como Usar\n1. Use /adicionar para incluir artigos da Wikipedia\n2. Use /buscar para encontrar conteúdo relevante\n3. Use /perguntar para fazer perguntas com RAG",
    version="2.0.0-funcional",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar diretório de arquivos estáticos
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# --- MULTIUSUÁRIO: ENDPOINTS ---
import mysql.connector

def get_mysql_conn():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="customkb"
    )

def get_or_create_user(email: str):
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (email, criado_em) VALUES (%s, NOW())", (email,))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

@app.post("/login", response_model=User)
async def login(email: str):
    """Login por email. Cria usuário se não existir."""
    user = get_or_create_user(email)
    return User(**user)

@app.post("/criar_base", response_model=KnowledgeBase)
async def criar_base(email: str, nome: str):
    """Cria uma base de conhecimento para o usuário (coleção Qdrant exclusiva)."""
    user = get_or_create_user(email)
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    # Nome da coleção Qdrant: base_<usuario_id>_<nome>
    qdrant_collection = f"base_{user['id']}_{nome}"
    cursor.execute("INSERT INTO knowledge_bases (nome, usuario_id, qdrant_collection, criado_em) VALUES (%s, %s, %s, NOW())", (nome, user['id'], qdrant_collection))
    conn.commit()
    cursor.execute("SELECT * FROM knowledge_bases WHERE usuario_id=%s AND nome=%s", (user['id'], nome))
    base = cursor.fetchone()
    cursor.close()
    conn.close()
    # TODO: criar coleção no Qdrant
    return KnowledgeBase(**base)


@app.get("/")
async def raiz():
    """Redireciona para a interface web"""
    return FileResponse(str(static_path / "index.html"))


@app.get("/artigos.html")
async def artigos_page():
    """Página de visualização de artigos"""
    return FileResponse(str(static_path / "artigos.html"))


@app.get("/api")
async def api_info():
    """Endpoint com informações da API"""
    return {
        "message": "Wikipedia Offline Vector Search API - Funcional",
        "version": "2.0.0-funcional",
        "description": "API offline para Wikipedia com LLM local",
        "endpoints": {
            "status": "/status - Verifica status dos componentes",
            "buscar": "/buscar - Busca semântica em artigos",
            "perguntar": "/perguntar - Faz perguntas com RAG offline",
            "adicionar": "/adicionar - Adiciona artigo da Wikipedia",
            "estatisticas": "/estatisticas - Estatísticas da base",
            "docs": "/docs - Documentação Swagger"
        },
        "features": [
            "Sistema completamente offline",
            "LLM local com Phi-3 Mini",
            "Busca semântica com Qdrant",
            "Processamento de artigos da Wikipedia",
            "Sistema RAG offline"
        ]
    }


@app.get("/status", response_model=StatusResponse)
async def verificar_status():
    """Verifica status de todos os componentes"""
    try:
        status_info = wikipedia_offline_service.verificar_status()
        return StatusResponse(**status_info)
    except Exception as e:
        return StatusResponse(
            status="error",
            sistema_offline=True,
            qdrant_conectado=False,
            ollama_disponivel=False,
            modelo_llm="unknown",
            inicializado=False
        )


@app.get("/estatisticas")
async def obter_estatisticas():
    """Estatísticas da base de conhecimento"""
    try:
        return wikipedia_offline_service.obter_estatisticas()
    except Exception as e:
        return {"erro": f"Erro ao obter estatísticas: {str(e)}"}


@app.get("/artigos")
async def listar_artigos():
    """Lista todos os artigos únicos na base de conhecimento"""
    try:
        return wikipedia_offline_service.listar_todos_artigos()
    except Exception as e:
        logger.error(f"Erro ao listar artigos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar artigos: {str(e)}")


@app.post("/buscar", response_model=BuscarResponse)
async def buscar_artigos(request: BuscarRequest):
    """Busca semântica em artigos da Wikipedia com validação de relevância"""
    try:
        import time
        start_time = time.time()
        
        telemetria = {
            "tempo_busca_qdrant_ms": 0,
            "tempo_filtragem_ms": 0,
            "tempo_total_ms": 0,
            "query_length": len(request.query),
            "limite_solicitado": request.limit,
            "resultados_antes_filtro": 0,
            "resultados_depois_filtro": 0
        }
        
        # Fase 1: Busca no Qdrant
        inicio_busca = time.time()
        resultados = wikipedia_offline_service.buscar_artigos(
            query=request.query,
            limit=request.limit
        )
        telemetria["tempo_busca_qdrant_ms"] = round((time.time() - inicio_busca) * 1000, 2)
        telemetria["resultados_antes_filtro"] = len(resultados) if resultados else 0
        
        # Fase 2: Filtragem de resultados
        inicio_filtragem = time.time()
        
        # Aplicar validação de termos similar ao sistema RAG, agora usando normalização
        if resultados:
            import unicodedata
            def normalizar_texto(texto):
                texto_nfd = unicodedata.normalize('NFD', texto)
                texto_sem_acento = ''.join(c for c in texto_nfd if unicodedata.category(c) != 'Mn')
                return texto_sem_acento.lower()

            stopwords = ['o', 'que', 'é', 'a', 'de', 'da', 'do', 'um', 'uma', 'os', 'as', 'para', 'com', 'por']
            termos_query = [t.lower().strip('?.,!()') for t in request.query.split() if t.lower() not in stopwords and len(t) > 2]
            termos_query_normalizados = [normalizar_texto(t) for t in termos_query]

            if termos_query_normalizados:
                resultados_filtrados = []
                for r in resultados:
                    titulo_norm = normalizar_texto(r.title)
                    conteudo_norm = normalizar_texto(r.content)

                    # Verificar se algum termo normalizado da query aparece no título ou conteúdo normalizado
                    tem_termo = any(termo in titulo_norm or termo in conteudo_norm for termo in termos_query_normalizados)

                    # Verificação reversa: título normalizado aparece na query normalizada
                    titulo_palavras = [normalizar_texto(p) for p in r.title.split() if len(p) > 2]
                    query_norm = normalizar_texto(request.query)
                    titulo_na_query = any(palavra in query_norm for palavra in titulo_palavras)

                    if tem_termo or titulo_na_query:
                        resultados_filtrados.append(r)
                resultados = resultados_filtrados
        
        telemetria["tempo_filtragem_ms"] = round((time.time() - inicio_filtragem) * 1000, 2)
        telemetria["resultados_depois_filtro"] = len(resultados) if resultados else 0
        
        end_time = time.time()
        tempo_busca_ms = (end_time - start_time) * 1000
        telemetria["tempo_total_ms"] = round(tempo_busca_ms, 2)
        
        # Converter para modelos Pydantic
        resultados_modelo = [
            WikipediaResultModel(
                title=r.title,
                content=r.content,
                url=r.url,
                score=r.score
            )
            for r in resultados
        ]
        
        return BuscarResponse(
            query=request.query,
            total_resultados=len(resultados_modelo),
            resultados=resultados_modelo,
            tempo_busca_ms=tempo_busca_ms,
            telemetria=telemetria
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na busca: {str(e)}"
        )


@app.post("/buscar_previa", response_model=BuscaPreviaResponse)
async def buscar_previa(request: PerguntarRequest):
    """Executa apenas a busca semântica e retorna os resultados encontrados"""
    try:
        start_time = time.time()
        
        # Executar busca (agora retorna telemetria também)
        documentos, total_chunks, total_artigos, encontrou, telemetria_busca = wikipedia_offline_service.buscar_para_rag(
            pergunta=request.pergunta,
            max_chunks=request.max_chunks
        )
        
        search_time = (time.time() - start_time) * 1000
        
        # Converter fontes para modelos Pydantic
        fontes_modelo = [
            WikipediaResultModel(
                title=doc.title,
                content=doc.content,
                url=doc.url,
                score=doc.score
            )
            for doc in documentos
        ]
        
        return BuscaPreviaResponse(
            pergunta=request.pergunta,
            encontrou_resultados=encontrou,
            total_chunks=total_chunks,
            total_artigos=total_artigos,
            fontes=fontes_modelo,
            tempo_busca_ms=search_time,
            telemetria=telemetria_busca
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar: {str(e)}"
        )


@app.post("/perguntar", response_model=RAGResponseModel)
async def perguntar_com_rag(request: PerguntarRequest):
    """Responde perguntas usando RAG offline com Phi-3"""
    try:
        start_time = time.time()
        
        resposta_rag = await wikipedia_offline_service.perguntar_com_rag(
            pergunta=request.pergunta,
            max_chunks=request.max_chunks
        )
        
        end_time = time.time()
        tempo_processamento_ms = (end_time - start_time) * 1000
        
        # Converter fontes para modelos Pydantic
        fontes_modelo = [
            WikipediaResultModel(
                title=fonte.title,
                content=fonte.content,
                url=fonte.url,
                score=fonte.score
            )
            for fonte in resposta_rag.sources
        ]

        return RAGResponseModel(
            pergunta=resposta_rag.question,
            resposta=resposta_rag.answer,
            fontes=fontes_modelo,
            raciocinio=resposta_rag.reasoning,
            tempo_processamento_ms=tempo_processamento_ms,
            total_chunks=resposta_rag.total_chunks,
            total_artigos=resposta_rag.total_artigos,
            telemetria=resposta_rag.telemetria
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar pergunta: {str(e)}"
        )


@app.post("/adicionar", response_model=AdicionarArtigoResponse)
async def adicionar_artigo(request: AdicionarArtigoRequest):
    """Adiciona artigo da Wikipedia à base local"""
    try:
        chunks_adicionados = wikipedia_offline_service.adicionar_artigo_wikipedia(
            request.titulo
        )
        
        if chunks_adicionados == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artigo '{request.titulo}' não encontrado ou erro no processamento"
            )
        
        # Construir URL da Wikipedia
        url_titulo = request.titulo.replace(" ", "_")
        url = f"https://pt.wikipedia.org/wiki/{url_titulo}"
        
        return AdicionarArtigoResponse(
            message="Artigo adicionado com sucesso à base offline",
            titulo=request.titulo,
            url=url,
            chunks_adicionados=chunks_adicionados
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao adicionar artigo: {str(e)}"
        )



@app.post("/ingest")
async def ingerir_artigos_personalizados(request: dict):
    """Ingere uma lista personalizada de artigos da Wikipedia"""
    try:
        total_chunks = 0
        resultados = []
        artigos_processados = 0
        artigos_falharam = 0

        artigos = request.get("artigos", [])
        for titulo in artigos:
            try:
                chunks = wikipedia_offline_service.adicionar_artigo_wikipedia(titulo)
                total_chunks += chunks

                if chunks > 0:
                    artigos_processados += 1
                    status = "ok"
                else:
                    artigos_falharam += 1
                    status = "erro"

                resultados.append({
                    "titulo": titulo,
                    "chunks": chunks,
                    "status": status,
                    "erro": None if chunks > 0 else "Artigo não encontrado ou erro no processamento"
                })

            except Exception as e:
                artigos_falharam += 1
                resultados.append({
                    "titulo": titulo,
                    "chunks": 0,
                    "status": "erro",
                    "erro": str(e)
                })

        return {
            "message": "Ingestão personalizada concluída",
            "total_artigos": len(artigos),
            "total_chunks": total_chunks,
            "artigos_processados": artigos_processados,
            "artigos_falharam": artigos_falharam,
            "resultados": resultados
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na ingestão personalizada: {str(e)}"
        )


@app.post("/ingest/exemplos")
async def ingerir_artigos_exemplo(background_tasks: BackgroundTasks):
    """Ingere alguns artigos de exemplo da Wikipedia"""
    artigos_exemplo = [
        "Inteligência artificial",
        "Machine learning", 
        "Ciência de dados",
        "Python (linguagem de programação)",
        "Brasil"
    ]
    
    try:
        total_chunks = 0
        resultados = []
        
        for titulo in artigos_exemplo:
            chunks = wikipedia_offline_service.adicionar_artigo_wikipedia(titulo)
            total_chunks += chunks
            resultados.append({
                "titulo": titulo,
                "chunks": chunks,
                "status": "ok" if chunks > 0 else "erro"
            })
        
        return {
            "message": "Ingestão de artigos de exemplo concluída",
            "total_artigos": len(artigos_exemplo),
            "total_chunks": total_chunks,
            "resultados": resultados
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na ingestão: {str(e)}"
        )


@app.post("/langchain/ingest/exemplos")
async def ingerir_artigos_com_langchain():
    """Ingere artigos usando pipeline LangChain completo"""
    artigos_exemplo = [
        "Inteligência artificial",
        "Machine learning", 
        "Ciência de dados",
        "Python (linguagem de programação)",
        "Brasil",
        "Arqueologia de aviação",
        "Segurança da aviação"
    ]
    
    try:
        logger.info("🔗 Iniciando ingestão com LangChain...")
        
        # Usar o novo método LangChain
        resultados = wikipedia_offline_service.adicionar_artigos_com_langchain(artigos_exemplo)
        
        total_chunks = sum(resultados.values())
        sucessos = len([r for r in resultados.values() if r > 0])
        
        return {
            "message": "Ingestão com LangChain concluída",
            "metodo": "LangChain TextSplitter + Retriever",
            "total_artigos": len(artigos_exemplo),
            "artigos_processados": sucessos,
            "total_chunks": total_chunks,
            "resultados": resultados,
            "features": [
                "Processamento com LangChain TextSplitter",
                "Embeddings com SentenceTransformers",
                "Armazenamento otimizado no Qdrant",
                "Retriever personalizado LangChain"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na ingestão LangChain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na ingestão LangChain: {str(e)}"
        )


@app.get("/langchain/stats")
async def estatisticas_langchain():
    """Estatísticas da coleção LangChain"""
    try:
        from services.langchainWikipediaService import langchain_wikipedia_service
        
        stats = langchain_wikipedia_service.obter_estatisticas()
        
        return {
            "message": "Estatísticas da coleção LangChain",
            "langchain_collection": stats,
            "features": [
                "Documentos processados com LangChain",
                "TextSplitter recursivo",
                "Embeddings multilíngues",
                "Retriever otimizado"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro: {str(e)}"
        )


@app.post("/ingest/categorias")
async def ingerir_por_categorias():
    """Ingere artigos por categorias temáticas predefinidas"""
    
    categorias = {
        "tecnologia": [
            "Inteligência artificial",
            "Machine learning",
            "Ciência de dados", 
            "Python",
            "JavaScript",
            "Computação",
            "Internet",
            "Algoritmo",
            "Programação",
            "Software"
        ],
        "brasil": [
            "Brasil",
            "Brasília", 
            "São Paulo",
            "Rio de Janeiro",
            "História do Brasil",
            "Geografia do Brasil",
            "Economia do Brasil",
            "Política do Brasil",
            "Cultura do Brasil",
            "Demografia do Brasil"
        ],
        "ciencias": [
            "Matemática",
            "Física", 
            "Química",
            "Biologia",
            "Medicina",
            "Astronomia",
            "Geologia",
            "Psicologia",
            "Sociologia",
            "Filosofia"
        ],
        "historia": [
            "História",
            "Primeira Guerra Mundial",
            "Segunda Guerra Mundial", 
            "Revolução Industrial",
            "Idade Média",
            "Renascimento",
            "Iluminismo",
            "Revolução Francesa",
            "Império Romano",
            "Civilização"
        ]
    }
    
    try:
        resultados_por_categoria = {}
        total_geral = 0
        
        for categoria, artigos in categorias.items():
            total_chunks = 0
            artigos_processados = 0
            resultados = []
            
            for titulo in artigos:
                try:
                    chunks = wikipedia_offline_service.adicionar_artigo_wikipedia(titulo)
                    total_chunks += chunks
                    total_geral += chunks
                    
                    if chunks > 0:
                        artigos_processados += 1
                        
                    resultados.append({
                        "titulo": titulo,
                        "chunks": chunks,
                        "status": "ok" if chunks > 0 else "erro"
                    })
                    
                except Exception as e:
                    resultados.append({
                        "titulo": titulo,
                        "chunks": 0,
                        "status": "erro",
                        "erro": str(e)
                    })
            
            resultados_por_categoria[categoria] = {
                "total_artigos": len(artigos),
                "artigos_processados": artigos_processados,
                "total_chunks": total_chunks,
                "resultados": resultados
            }
        
        return {
            "message": "Ingestão por categorias concluída",
            "total_chunks_geral": total_geral,
            "categorias": resultados_por_categoria
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na ingestão por categorias: {str(e)}"
        )


@app.delete("/limpar")
async def limpar_base():
    """Remove todos os artigos da base de conhecimento"""
    try:
        # Limpar coleção do Qdrant
        wikipedia_offline_service.limpar_colecao()
        
        return {
            "message": "Base de conhecimento limpa com sucesso",
            "chunks_removidos": "todos",
            "status": "limpo"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar base: {str(e)}"
        )


@app.get("/dumps/disponiveis")
async def listar_dumps_disponiveis(language: str = "pt"):
    """Lista dumps disponíveis para download"""
    try:
        dumps = wikipedia_dump_processor.get_available_dumps(language)
        
        dump_responses = [
            {
                "language": dump.language,
                "date": dump.date,
                "type": dump.type,
                "url": dump.url,
                "size_mb": dump.size_mb,
                "filename": dump.filename,
                "description": f"Dump {dump.type} da Wikipedia {dump.language.upper()}"
            }
            for dump in dumps
        ]
        
        return {
            "message": f"Dumps disponíveis para {language.upper()}",
            "total_dumps": len(dump_responses),
            "dumps": dump_responses,
            "recomendacao": "Use 'pages-articles' para ingestão completa (recomendado)"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar dumps: {str(e)}"
        )


@app.post("/dumps/download")
async def download_dump(language: str = "pt", dump_type: str = "pages-articles"):
    """Inicia download de um dump da Wikipedia"""
    try:
        # Obter dumps disponíveis
        dumps = wikipedia_dump_processor.get_available_dumps(language)
        
        # Encontrar dump do tipo solicitado
        target_dump = None
        for dump in dumps:
            if dump.type == dump_type:
                target_dump = dump
                break
        
        if not target_dump:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dump do tipo '{dump_type}' não encontrado para {language}"
            )
        
        # Verificar se já existe
        filepath = wikipedia_dump_processor.data_dir / target_dump.filename
        if filepath.exists():
            file_size_mb = round(filepath.stat().st_size / (1024 * 1024), 2)
            return {
                "message": "Dump já existe localmente",
                "dump_info": {
                    "filename": target_dump.filename,
                    "size_mb": file_size_mb,
                    "type": target_dump.type,
                    "language": target_dump.language
                },
                "filepath": str(filepath),
                "status": "já_baixado",
                "proximo_passo": f"Use POST /dumps/processar com filename='{target_dump.filename}'"
            }
        
        # Verificar espaço em disco (Windows)
        import shutil
        free_space_gb = round(shutil.disk_usage(wikipedia_dump_processor.data_dir).free / (1024**3), 2)
        required_space_gb = round(target_dump.size_mb / 1024 * 2, 2)  # 2x para descompressão
        
        if free_space_gb < required_space_gb:
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail=f"Espaço insuficiente. Necessário: {required_space_gb}GB, Disponível: {free_space_gb}GB"
            )
        
        # Iniciar download em background
        return {
            "message": "Download configurado (implementação para uso real)",
            "dump_info": {
                "filename": target_dump.filename,
                "size_mb": target_dump.size_mb,
                "type": target_dump.type,
                "language": target_dump.language,
                "url": target_dump.url
            },
            "espaco_necessario_gb": required_space_gb,
            "espaco_disponivel_gb": free_space_gb,
            "status": "pronto_para_download",
            "instrucoes": [
                f"Para download real, execute:",
                f"curl -o data/{target_dump.filename} {target_dump.url}",
                f"Ou use wget/PowerShell para baixar ~{target_dump.size_mb}MB"
            ],
            "comando_powershell": f"Invoke-WebRequest -Uri '{target_dump.url}' -OutFile 'data/{target_dump.filename}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no download: {str(e)}"
        )


@app.get("/dumps/status")
async def status_dumps():
    """Status dos dumps e diretório de dados"""
    try:
        data_dir = wikipedia_dump_processor.data_dir
        data_dir.mkdir(exist_ok=True)
        
        dumps_files = []
        total_size = 0
        
        if data_dir.exists():
            for file in data_dir.glob("*.xml.*"):
                file_stat = file.stat()
                size_mb = round(file_stat.st_size / (1024 * 1024), 2)
                dumps_files.append({
                    "filename": file.name,
                    "size_mb": size_mb,
                    "modified": file_stat.st_mtime
                })
                total_size += size_mb
        
        return {
            "data_directory": str(data_dir),
            "directory_exists": data_dir.exists(),
            "total_dumps": len(dumps_files),
            "dumps_baixados": dumps_files,
            "espaco_usado_mb": total_size,
            "recomendacoes": [
                "Dumps típicos: 1-5 GB comprimidos",
                "Certifique-se de ter 10+ GB livres",
                "Use 'pages-articles' para melhor custo-benefício"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar status: {str(e)}"
        )


@app.post("/dumps/processar-exemplo")
async def processar_dump_exemplo():
    """Processa um dump XML de exemplo para demonstração"""
    try:
        import time
        start_time = time.time()
        
        # Usar o dump de exemplo
        filepath = wikipedia_dump_processor.data_dir / "exemplo_dump.xml"
        
        if not filepath.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dump de exemplo não encontrado"
            )
        
        total_articles = 0
        total_chunks = 0
        
        # Processar dump de exemplo
        chunk_batch = []
        
        for chunk_data in wikipedia_dump_processor.process_dump_to_chunks(str(filepath)):
            chunk_batch.append(chunk_data)
            
            # Processar lote a cada 10 chunks (para exemplo)
            if len(chunk_batch) >= 10:
                chunks_added = wikipedia_offline_service._processar_lote_chunks(chunk_batch)
                total_chunks += chunks_added
                total_articles += len(set(chunk['title'] for chunk in chunk_batch))
                chunk_batch = []
        
        # Processar lote final
        if chunk_batch:
            chunks_added = wikipedia_offline_service._processar_lote_chunks(chunk_batch)
            total_chunks += chunks_added
            total_articles += len(set(chunk['title'] for chunk in chunk_batch))
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        return {
            "message": "Dump de exemplo processado com sucesso",
            "tipo": "Demonstração de processamento XML",
            "total_articles_processed": total_articles,
            "total_chunks_created": total_chunks,
            "processing_time_seconds": round(processing_time, 2),
            "artigos_incluidos": ["Inteligência artificial", "Machine learning", "Python"],
            "formato_original": "MediaWiki XML",
            "proximos_passos": [
                "Use GET /estatisticas para ver o crescimento da base",
                "Use POST /buscar para testar busca nos novos artigos",
                "Para dumps reais, use POST /dumps/download primeiro"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dump de exemplo: {str(e)}"
        )


@app.post("/dumps/download-real")
async def download_dump_real(language: str = "pt", dump_type: str = "pages-articles"):
    """Faz download real de um dump da Wikipedia (pode demorar)"""
    try:
        # Obter dumps disponíveis
        dumps = wikipedia_dump_processor.get_available_dumps(language)
        
        # Encontrar dump do tipo solicitado
        target_dump = None
        for dump in dumps:
            if dump.type == dump_type:
                target_dump = dump
                break
        
        if not target_dump:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dump do tipo '{dump_type}' não encontrado para {language}"
            )
        
        # Verificar se já existe
        filepath = wikipedia_dump_processor.data_dir / target_dump.filename
        if filepath.exists():
            file_size_mb = round(filepath.stat().st_size / (1024 * 1024), 2)
            return {
                "message": "Dump já existe localmente",
                "filename": target_dump.filename,
                "size_mb": file_size_mb,
                "status": "existente"
            }
        
        # Fazer download real
        try:
            import time
            start_time = time.time()
            
            logger.info(f"🔄 Iniciando download real: {target_dump.url}")
            
            # Usar o método de download do processador
            downloaded_path = wikipedia_dump_processor.download_dump(target_dump)
            
            end_time = time.time()
            download_time = end_time - start_time
            
            # Verificar tamanho do arquivo baixado
            actual_size_mb = round(Path(downloaded_path).stat().st_size / (1024 * 1024), 2)
            
            return {
                "message": "Download real concluído com sucesso!",
                "dump_info": {
                    "filename": target_dump.filename,
                    "size_mb": actual_size_mb,
                    "type": target_dump.type,
                    "language": target_dump.language
                },
                "download_time_seconds": round(download_time, 2),
                "filepath": downloaded_path,
                "status": "baixado",
                "proximo_passo": f"Use POST /dumps/processar com filename='{target_dump.filename}'"
            }
            
        except Exception as download_error:
            logger.error(f"❌ Erro no download: {download_error}")
            return {
                "message": "Erro no download real",
                "erro": str(download_error),
                "alternativa": f"Download manual: Invoke-WebRequest -Uri '{target_dump.url}' -OutFile 'data/{target_dump.filename}'",
                "status": "erro"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no download real: {str(e)}"
        )


@app.post("/dumps/processar-expandido")
async def processar_dump_expandido():
    """Processa dump XML expandido (5 artigos detalhados) para demonstração"""
    try:
        import time
        start_time = time.time()
        
        # Usar o dump expandido
        filepath = wikipedia_dump_processor.data_dir / "dump_expandido.xml"
        
        if not filepath.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dump expandido não encontrado"
            )
        
        total_articles = 0
        total_chunks = 0
        
        # Processar dump expandido
        chunk_batch = []
        
        for chunk_data in wikipedia_dump_processor.process_dump_to_chunks(str(filepath)):
            chunk_batch.append(chunk_data)
            
            # Processar lote a cada 20 chunks
            if len(chunk_batch) >= 20:
                chunks_added = wikipedia_offline_service._processar_lote_chunks(chunk_batch)
                total_chunks += chunks_added
                total_articles += len(set(chunk['title'] for chunk in chunk_batch))
                chunk_batch = []
        
        # Processar lote final
        if chunk_batch:
            chunks_added = wikipedia_offline_service._processar_lote_chunks(chunk_batch)
            total_chunks += chunks_added
            total_articles += len(set(chunk['title'] for chunk in chunk_batch))
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        return {
            "message": "Dump expandido processado com sucesso!",
            "tipo": "Demonstração de ingestão em massa",
            "total_articles_processed": total_articles,
            "total_chunks_created": total_chunks,
            "processing_time_seconds": round(processing_time, 2),
            "chunks_per_second": round(total_chunks / processing_time, 2) if processing_time > 0 else 0,
            "artigos_incluidos": [
                "Brasil (geografia, história, cultura)",
                "Inteligência artificial (completo)",
                "Python (linguagem completa)",
                "Ciência de dados (processo completo)",
                "Machine learning (algoritmos e aplicações)"
            ],
            "tamanho_dump": "~25KB XML descomprimido",
            "formato_original": "MediaWiki XML padrão",
            "comparacao": {
                "dump_exemplo": "3 artigos, 3 chunks",
                "dump_expandido": f"{total_articles} artigos, {total_chunks} chunks",
                "crescimento": f"{total_chunks}x mais conteúdo"
            },
            "proximos_passos": [
                "Use GET /estatisticas para ver o crescimento da base",
                "Use POST /buscar para testar busca nos novos artigos detalhados",
                "Compare a qualidade das respostas com mais conteúdo"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dump expandido: {str(e)}"
        )


@app.get("/dumps/verificar-url")
async def verificar_url_dump(url: str):
    """Verifica se uma URL de dump está acessível"""
    try:
        import requests
        
        # Fazer request HEAD para verificar se existe
        response = requests.head(url, timeout=30)
        
        if response.status_code == 200:
            content_length = response.headers.get('content-length', '0')
            size_mb = round(int(content_length) / (1024 * 1024), 2) if content_length.isdigit() else 0
            
            return {
                "url": url,
                "status": "disponível",
                "http_status": response.status_code,
                "size_mb": size_mb,
                "headers": dict(response.headers),
                "recomendacao": "URL válida para download"
            }
        else:
            return {
                "url": url,
                "status": "erro",
                "http_status": response.status_code,
                "erro": f"Status HTTP: {response.status_code}",
                "recomendacao": "Tente uma URL diferente ou data mais antiga"
            }
    
    except Exception as e:
        return {
            "url": url,
            "status": "erro",
            "erro": str(e),
            "recomendacao": "Verifique a conectividade ou tente URL alternativa"
        }


@app.post("/dumps/simular-download")
async def simular_download_dump():
    """Simula download de um dump para demonstração"""
    try:
        import time
        import gzip
        
        # Criar um arquivo simulado maior que o exemplo
        start_time = time.time()
        
        # Nome do arquivo simulado
        filename = "ptwiki-simulado-pages-articles.xml.gz"
        filepath = wikipedia_dump_processor.data_dir / filename
        
        if filepath.exists():
            return {
                "message": "Dump simulado já existe",
                "filename": filename,
                "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
                "status": "existente"
            }
        
        # Criar conteúdo XML simulado maior
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="0.10" xml:lang="pt">
  <siteinfo>
    <sitename>Wikipedia Simulada</sitename>
    <dbname>ptwiki_simulado</dbname>
    <base>https://pt.wikipedia.org/wiki/Página_principal</base>
    <generator>Simulador MediaWiki</generator>
  </siteinfo>'''
        
        # Adicionar múltiplos artigos simulados para criar um arquivo maior
        artigos_simulados = [
            ("Tecnologia", "A tecnologia é a aplicação de conhecimentos científicos para resolver problemas práticos. Inclui desenvolvimento de ferramentas, máquinas, materiais e processos que facilitam a vida humana. A evolução tecnológica tem sido constante ao longo da história, desde a invenção da roda até a era digital atual."),
            ("História do Brasil", "A história do Brasil começou com a chegada dos primeiros habitantes há milhares de anos. A colonização portuguesa iniciou em 1500 com Pedro Álvares Cabral. O país passou por diversos períodos: colonial, imperial e republicano, cada um com suas características econômicas, sociais e políticas únicas."),
            ("Física", "A física é a ciência que estuda a natureza e seus fenômenos em seus aspectos mais gerais. Analisa matter, energia, movimento, forças, espaço e tempo. Subdivide-se em mecânica, termodinâmica, eletromagnetismo, óptica, física moderna e outras áreas especializadas."),
            ("Matemática", "A matemática é a ciência que lida com lógica de forma quantitativa. Estuda números, estruturas, padrões, relações e mudanças. É fundamental para ciências exatas, engenharia, economia e diversas outras áreas do conhecimento humano."),
            ("Literatura", "A literatura é a arte da palavra escrita. Expressa sentimentos, ideias e experiências humanas através de diferentes gêneros como romance, poesia, drama e ensaio. Reflete cultura, sociedade e época de sua criação."),
            ("Geografia", "A geografia estuda a Terra e seus fenômenos naturais e humanos. Analisa relevo, clima, vegetação, população, economia e organização espacial. Divide-se em geografia física e humana, cada uma com suas especificidades."),
            ("Química", "A química é a ciência que estuda matter e suas transformações. Analisa composição, estrutura, propriedades e comportamento de átomos e moléculas. É essencial para indústria, medicina, agricultura e tecnologia."),
            ("Biologia", "A biologia é a ciência da vida. Estuda organismos vivos, desde microscópicos até complexos. Abrange genética, evolução, ecologia, anatomia, fisiologia e outras áreas relacionadas aos seres vivos."),
            ("Economia", "A economia estuda produção, distribuição e consumo de bens e serviços. Analisa comportamento de mercados, políticas governamentais, desenvolvimento econômico e bem-estar social. É fundamental para tomada de decisões empresariais e públicas."),
            ("Sociologia", "A sociologia estuda society e comportamento social humano. Analisa grupos, instituições, mudanças sociais, desigualdades e interações humanas. Contribui para compreensão de problemas sociais contemporâneos."),
            ("Computação", "A ciência da computação estuda algoritmos, estruturas de dados e sistemas computacionais. É fundamental para desenvolvimento de software, inteligência artificial, análise de dados e automação de processos."),
            ("Engenharia", "A engenharia aplica princípios científicos e matemáticos para projetar, construir e manter estruturas, máquinas e sistemas. Divide-se em diversas especialidades como civil, mecânica, elétrica e outras.")
        ]
        
        for i, (titulo, conteudo) in enumerate(artigos_simulados, 2000):
            xml_content += f'''
  <page>
    <title>{titulo}</title>
    <ns>0</ns>
    <id>{i}</id>
    <revision>
      <id>{i + 10000}</id>
      <timestamp>2024-10-31T10:00:00Z</timestamp>
      <contributor>
        <username>SimuladorBot</username>
        <id>9999</id>
      </contributor>
      <text bytes="{len(conteudo) * 3}" xml:space="preserve">{conteudo}

== Introdução ==
{conteudo}

== Desenvolvimento ==
{conteudo} Este é um artigo expandido para demonstração do sistema de processamento de dumps da Wikipedia. O conteúdo foi multiplicado para simular artigos maiores e mais complexos que são encontrados em dumps reais.

== História ==
A história de {titulo.lower()} é rica e complexa, envolvendo diversos aspectos culturais, tecnológicos e sociais ao longo dos séculos.

== Características principais ==
* Aspecto 1: Fundamental para compreensão
* Aspecto 2: Influência na sociedade moderna  
* Aspecto 3: Desenvolvimentos recentes
* Aspecto 4: Perspectivas futuras

== Aplicações ==
As aplicações de {titulo.lower()} são vastas e incluem diversos setores da sociedade moderna, desde educação até indústria.

== Referências ==
* Fonte acadêmica simulada 1
* Fonte acadêmica simulada 2
* Fonte acadêmica simulada 3
* Base de dados de referência

== Ver também ==
* [[Artigo relacionado 1]]
* [[Artigo relacionado 2]]
* [[Categoria principal]]

== Ligações externas ==
* Site oficial simulado
* Recurso educacional simulado

[[Categoria:{titulo}]]
[[Categoria:Artigos simulados]]
[[Categoria:Base de conhecimento]]</text>
    </revision>
  </page>'''
        
        xml_content += '\n</mediawiki>'
        
        # Salvar arquivo comprimido
        with gzip.open(str(filepath), 'wt', encoding='utf-8') as f:
            f.write(xml_content)
        
        end_time = time.time()
        file_size_mb = round(filepath.stat().st_size / (1024 * 1024), 2)
        
        return {
            "message": "Dump simulado criado com sucesso!",
            "tipo": "Simulação de dump real da Wikipedia",
            "filename": filename,
            "size_mb": file_size_mb,
            "total_articles": len(artigos_simulados),
            "creation_time_seconds": round(end_time - start_time, 2),
            "formato": "XML MediaWiki comprimido (gzip)",
            "uso": f"Use POST /dumps/processar com filename='{filename}'",
            "vantagem": "Simula processamento de dump real sem download de centenas de MB",
            "conteudo": [
                f"{len(artigos_simulados)} artigos temáticos diversos",
                "Conteúdo expandido e estruturado para cada artigo", 
                "Estrutura XML MediaWiki completa",
                "Arquivo comprimido como dumps reais",
                "Seções organizadas (Introdução, História, Características, etc.)",
                "Metadados de página e revisão realistas"
            ],
            "proximos_passos": [
                f"1. Processar: POST /dumps/processar (filename={filename})",
                "2. Verificar progresso: GET /dumps/status",
                "3. Buscar conteúdo: POST /buscar (query='tecnologia')",
                "4. Ver estatísticas: GET /stats"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao simular download: {str(e)}"
        )


@app.post("/dumps/baixar-real")
async def baixar_dump_real(url: str, background_tasks: BackgroundTasks):
    """Baixa um dump real da Wikipedia"""
    try:
        import requests
        from pathlib import Path
        import time
        
        # Extrair nome do arquivo da URL
        filename = url.split('/')[-1]
        filepath = wikipedia_dump_processor.data_dir / filename
        
        if filepath.exists():
            return {
                "message": "Arquivo já existe",
                "filename": filename,
                "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
                "status": "existente",
                "uso": f"Use POST /dumps/processar-real com filename='{filename}'"
            }
        
        # Verificar se URL está acessível
        response = requests.head(url, timeout=30)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL não acessível: {response.status_code}"
            )
        
        file_size_bytes = int(response.headers.get('content-length', 0))
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        
        # Função para baixar em background
        def download_file():
            try:
                start_time = time.time()
                
                with requests.get(url, stream=True, timeout=300) as r:
                    r.raise_for_status()
                    with open(filepath, 'wb') as f:
                        downloaded = 0
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                
                end_time = time.time()
                download_time = end_time - start_time
                
                # Log de sucesso (seria melhor usar logging real)
                print(f"Download concluído: {filename} ({file_size_mb} MB) em {download_time:.1f}s")
                
            except Exception as e:
                print(f"Erro no download: {str(e)}")
                if filepath.exists():
                    filepath.unlink()  # Remove arquivo parcial
        
        # Iniciar download em background
        background_tasks.add_task(download_file)
        
        return {
            "message": "Download iniciado em background",
            "tipo": "Dump real da Wikipedia",
            "url": url,
            "filename": filename,
            "size_mb_esperado": file_size_mb,
            "status": "downloading",
            "tempo_estimado_min": round(file_size_mb / 10, 1),  # ~10MB/min estimativa
            "verificar_progresso": "Verifique se arquivo existe em /dumps/disponiveis",
            "proximos_passos": [
                "1. Aguardar conclusão do download",
                f"2. Verificar: GET /dumps/disponiveis",
                f"3. Processar: POST /dumps/processar-real (filename={filename})"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao baixar dump: {str(e)}"
        )


@app.post("/dumps/processar-real")
async def processar_dump_real(filename: str, max_artigos: int = 1000, offset: int = 0):
    """Processa um dump real da Wikipedia (com limite para evitar sobrecarga)"""
    try:
        import time
        
        start_time = time.time()
        
        # Verificar se arquivo existe
        filepath = wikipedia_dump_processor.data_dir / filename
        if not filepath.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo não encontrado: {filename}"
            )
        
        # Obter tamanho do arquivo
        file_size_mb = round(filepath.stat().st_size / (1024 * 1024), 2)
        
        # Processar dump com limite
        wikipedia_dump_processor.offset = offset
        chunks_generator = wikipedia_dump_processor.process_dump_to_chunks(
            str(filepath), 
            max_articles=max_artigos
        )
        
        # Processar chunks e adicionar ao Qdrant
        total_chunks = 0
        articles_processed = 0
        
        print(f"🔄 Iniciando processamento de {filepath}")
        print(f"📊 Limite de artigos: {max_artigos}")
        
        try:
            chunk_count = 0
            for chunk_data in chunks_generator:
                chunk_count += 1
                print(f"🧩 Chunk {chunk_count}: {chunk_data.get('title', 'sem título')[:50]}...")
                
                # Adicionar chunk ao Qdrant através do serviço offline
                try:
                    success = wikipedia_offline_service.adicionar_chunk_direto(chunk_data)
                    if success:
                        total_chunks += 1
                        if total_chunks % 10 == 0:  # Log a cada 10 chunks
                            print(f"✅ {total_chunks} chunks processados...")
                except Exception as e:
                    print(f"❌ Erro ao adicionar chunk: {e}")
                    continue
            
            print(f"🔍 Total de chunks gerados pelo parser: {chunk_count}")
            
        except Exception as e:
            print(f"❌ Erro durante iteração do generator: {e}")
            import traceback
            print(f"📋 Stack trace: {traceback.format_exc()}")
        
        print(f"🏁 Processamento concluído: {total_chunks} chunks")
        
        end_time = time.time()
        processing_time = end_time - start_time
        chunks_per_second = round(total_chunks / processing_time, 2) if processing_time > 0 and total_chunks > 0 else 0
        
        return {
            "message": f"Dump real processado com sucesso! (Limitado a {max_artigos} artigos)",
            "tipo": "Processamento de dump real da Wikipedia",
            "filename": filename,
            "file_size_mb": file_size_mb,
            "total_chunks_created": total_chunks,
            "max_artigos_processados": max_artigos,
            "processing_time_seconds": round(processing_time, 2),
            "chunks_per_second": chunks_per_second,
            "formato": "MediaWiki XML real (comprimido bz2)",
            "aviso": "Processamento limitado para evitar sobrecarga do sistema",
            "proximos_passos": [
                "1. Verificar estatísticas: GET /estatisticas",
                "2. Testar busca: POST /buscar (query='brasil')",
                "3. Fazer perguntas: POST /perguntar",
                f"4. Para processar mais artigos: POST /dumps/processar-real (max_artigos > {max_artigos})"
            ],
            "observacao": f"Sistema agora tem dados reais da Wikipedia portuguesa! 🎉"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dump real: {str(e)}"
        )


@app.get("/dumps/status-download")
async def status_download():
    """Verifica status de downloads em andamento"""
    try:
        import os
        from pathlib import Path
        
        # Arquivos esperados e seus tamanhos
        downloads_esperados = {
            "ptwiki-20251020-pages-articles.xml.bz2": 2523205242,  # 2.4 GB
            "ptwiki-20251020-pages-articles1.xml-p1p105695.bz2": 190003828  # 181 MB
        }
        
        status_downloads = []
        
        for filename, tamanho_esperado in downloads_esperados.items():
            filepath = wikipedia_dump_processor.data_dir / filename
            
            if filepath.exists():
                tamanho_atual = filepath.stat().st_size
                porcentagem = round((tamanho_atual / tamanho_esperado) * 100, 1)
                mb_atual = round(tamanho_atual / (1024 * 1024), 1)
                mb_esperado = round(tamanho_esperado / (1024 * 1024), 1)
                
                # Determinar status
                if porcentagem >= 99.5:
                    status = "✅ Completo"
                elif porcentagem > 0:
                    status = f"🔄 {porcentagem}% ({mb_atual}/{mb_esperado} MB)"
                else:
                    status = "🆕 Iniciando"
                
                status_downloads.append({
                    "filename": filename,
                    "status": status,
                    "porcentagem": porcentagem,
                    "mb_atual": mb_atual,
                    "mb_esperado": mb_esperado,
                    "completo": porcentagem >= 99.5,
                    "ultima_modificacao": filepath.stat().st_mtime
                })
            else:
                status_downloads.append({
                    "filename": filename,
                    "status": "❌ Não encontrado",
                    "porcentagem": 0,
                    "mb_atual": 0,
                    "mb_esperado": round(tamanho_esperado / (1024 * 1024), 1),
                    "completo": False,
                    "ultima_modificacao": None
                })
        
        downloads_completos = sum(1 for d in status_downloads if d["completo"])
        total_downloads = len(status_downloads)
        
        return {
            "message": "Status de downloads da Wikipedia",
            "downloads_completos": downloads_completos,
            "total_downloads": total_downloads,
            "progresso_geral": f"{downloads_completos}/{total_downloads} completos",
            "downloads": status_downloads,
            "recomendacao": {
                "comando_monitoramento": "GET /dumps/status-download",
                "frequencia": "Execute a cada 5-10 minutos",
                "quando_completo": "Use POST /dumps/processar-real quando status=✅ Completo"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar status: {str(e)}"
        )


@app.post("/dumps/descomprimir-e-processar")
async def descomprimir_e_processar(filename: str, max_artigos: int = 100):
    """Descomprime arquivo BZ2/GZ e processa como XML direto"""
    try:
        import bz2
        import gzip
        import time
        
        start_time = time.time()
        
        # Caminho do arquivo comprimido
        compressed_path = wikipedia_dump_processor.data_dir / filename
        if not compressed_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo não encontrado: {filename}"
            )
        
        # Nome do arquivo descomprimido
        if filename.endswith('.bz2'):
            decompressed_name = filename.replace('.bz2', '.xml')
        elif filename.endswith('.gz'):
            decompressed_name = filename.replace('.gz', '.xml') 
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo deve ser .bz2 ou .gz"
            )
            
        decompressed_path = wikipedia_dump_processor.data_dir / decompressed_name
        
        # Verificar se já foi descomprimido
        if decompressed_path.exists():
            print(f"✅ Arquivo já descomprimido: {decompressed_name}")
        else:
            print(f"🗜️ Descomprimindo {filename}...")
            decompress_start = time.time()
            
            # Descomprimir
            if filename.endswith('.bz2'):
                with bz2.open(compressed_path, 'rt', encoding='utf-8') as f_in:
                    with open(decompressed_path, 'w', encoding='utf-8') as f_out:
                        # Ler em chunks para não sobrecarregar memória
                        while True:
                            chunk = f_in.read(1024*1024)  # 1MB chunks
                            if not chunk:
                                break
                            f_out.write(chunk)
            elif filename.endswith('.gz'):
                with gzip.open(compressed_path, 'rt', encoding='utf-8') as f_in:
                    with open(decompressed_path, 'w', encoding='utf-8') as f_out:
                        while True:
                            chunk = f_in.read(1024*1024)
                            if not chunk:
                                break
                            f_out.write(chunk)
            
            decompress_time = time.time() - decompress_start
            decompressed_size = decompressed_path.stat().st_size / (1024*1024)
            print(f"✅ Descompressão concluída em {decompress_time:.1f}s - {decompressed_size:.1f} MB")
        
        # Agora processar o XML descomprimido
        print(f"🔄 Processando XML descomprimido...")
        process_start = time.time()
        
        chunks_generator = wikipedia_dump_processor.process_dump_to_chunks(
            str(decompressed_path), 
            max_articles=max_artigos
        )
        
        total_chunks = 0
        for chunk_data in chunks_generator:
            try:
                success = wikipedia_offline_service.adicionar_chunk_direto(chunk_data)
                if success:
                    total_chunks += 1
                    if total_chunks % 50 == 0:
                        print(f"✅ {total_chunks} chunks processados...")
            except Exception as e:
                print(f"❌ Erro ao adicionar chunk: {e}")
                continue
        
        process_time = time.time() - process_start
        total_time = time.time() - start_time
        
        chunks_per_second = round(total_chunks / process_time, 2) if process_time > 0 else 0
        
        return {
            "message": f"Arquivo descomprimido e processado com sucesso!",
            "tipo": "Processamento via descompressão intermediária",
            "arquivo_original": filename,
            "arquivo_descomprimido": decompressed_name,
            "max_artigos": max_artigos,
            "total_chunks_created": total_chunks,
            "tempo_descompressao_s": round(decompress_time if 'decompress_time' in locals() else 0, 2),
            "tempo_processamento_s": round(process_time, 2),
            "tempo_total_s": round(total_time, 2),
            "chunks_per_second": chunks_per_second,
            "status": "✅ Sucesso com XML descomprimido",
            "observacao": "Método alternativo que contorna problemas do parser BZ2"
        }
        
    except Exception as e:
        import traceback
        print(f"❌ ERRO DETALHADO: {str(e)}")
        print(f"📍 TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no processo: {str(e)}"
        )


# Manipulador de erros global
@app.exception_handler(Exception)
async def manipulador_erro_global(request, exc):
    """Manipula erros não capturados"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor",
            "message": "Ocorreu um erro inesperado. Tente novamente.",
            "type": "internal_server_error",
            "sistema_offline": True
        }
    )


app.include_router(telemetria_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)