"""
Wikipedia Offline Service - Versão com LangChain

Versão que integra Qdrant + Ollama + dados da Wikipedia com LangChain
"""


import os
import time
import logging
import requests
import uuid
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import asyncio

# LangChain integration
from .langchainWikipediaService import langchain_wikipedia_service, WikipediaDocument

# Utilitários
from .utils.wikipedia_utils import (
    WikipediaAPIClient,
    TextProcessor,
    QdrantHelper,
    WikipediaDataValidator,
    MetricsCollector
)
from api.telemetria_ws import enviar_telemetria

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.models import PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Resultado de busca da Wikipedia"""
    title: str
    content: str
    url: str
    score: float
    categories: List[str] = None
    chunk_info: Dict[str, Any] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        if self.chunk_info is None:
            self.chunk_info = {}


@dataclass
class RAGResponse:
    """Resposta RAG com LLM local"""
    question: str
    answer: str
    sources: List[SearchResult]
    reasoning: str
    model_info: Dict[str, str]
    total_chunks: Optional[int] = None
    total_artigos: Optional[int] = None
    telemetria: Optional[Dict[str, Any]] = None


class WikipediaOfflineService:
    """Serviço Wikipedia offline funcional"""
    def __init__(self):
        self.client = None
        self.collection_name = "wikipedia_langchain"
        self.ollama_host = os.getenv("OLLAMA_HOST", "ollama")
        self.ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
        # Modelos separados para embedding e LLM
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "bge-large-pt")
        self.model_name = os.getenv("LLM_MODEL", "phi3")
        self._initialized = False
        
        # Inicializar utilitários
        self.api_client = WikipediaAPIClient()
        self.text_processor = TextProcessor()
        self.qdrant_helper = QdrantHelper()
        self.validator = WikipediaDataValidator()
        self.metrics = MetricsCollector()
        
    def inicializar(self):
        """Inicializa todos os componentes"""
        if self._initialized:
            return
            
        logger.info("🚀 Inicializando Wikipedia Offline Service...")
        
        try:
            # Inicializar LangChain Service
            logger.info("🔗 Inicializando LangChain Wikipedia Service...")
            langchain_wikipedia_service.inicializar()
            
            self._conectar_qdrant()
            self._criar_colecao_wikipedia()
            self._testar_ollama()
            
            self._initialized = True
            logger.info("✅ Wikipedia Offline Service inicializado com LangChain!")
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            # Em modo funcional, ainda inicializa mas marca problemas
            self._initialized = True
            logger.warning("⚠️ Iniciando em modo degradado")
    
    def _conectar_qdrant(self):
        """Conecta ao Qdrant"""
        if not QDRANT_AVAILABLE:
            logger.warning("⚠️ Qdrant não disponível")
            return
            
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        
        try:
            self.client = QdrantClient(host=host, port=port)
            self.client.get_collections()
            logger.info(f"✅ Conectado ao Qdrant em {host}:{port}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao conectar ao Qdrant: {e}")
            self.client = None
    
    def _criar_colecao_wikipedia(self):
        """Cria coleção específica para Wikipedia se não existir"""
        if not self.client:
            return
            
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"📚 Criando coleção: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # Dimensão do SentenceTransformers
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"✅ Coleção {self.collection_name} criada")
            else:
                logger.info(f"✅ Coleção {self.collection_name} já existe")
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar coleção: {e}")
    
    def _testar_ollama(self):
        """Testa conexão com Ollama"""
        try:
            url = f"http://{self.ollama_host}:{self.ollama_port}/api/version"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Ollama conectado (versão: {response.json().get('version')})")
                
                # Testar se o modelo está disponível
                models_url = f"http://{self.ollama_host}:{self.ollama_port}/api/tags"
                models_response = requests.get(models_url, timeout=5)
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    available_models = [m['name'] for m in models_data.get('models', [])]
                    if self.model_name in available_models:
                        logger.info(f"✅ Modelo {self.model_name} disponível")
                    else:
                        logger.warning(f"⚠️ Modelo {self.model_name} não encontrado. Disponíveis: {available_models}")
            else:
                logger.warning(f"⚠️ Ollama respondeu com status: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao conectar com Ollama: {e}")
    
    def adicionar_artigo_wikipedia(self, titulo: str, colecao: str = None) -> int:
        """Adiciona artigo da Wikipedia ao banco vetorial usando LangChain na coleção especificada"""
        try:
            if not self._initialized:
                logger.error("❌ Serviço não inicializado")
                raise Exception("Serviço não inicializado")
            
            logger.info(f"🔗 Iniciando adição de artigo com LangChain")
            logger.info(f"📥############## Coleção: {colecao} adição do artigo  {titulo} com LangChain")

            # Buscar artigo na Wikipedia
            logger.info(f"📖 Buscando artigo: {titulo}")
            artigo = self._buscar_artigo_wikipedia(titulo)
            
            if not artigo:
                logger.warning(f"⚠️ Artigo '{titulo}' não encontrado")
                return 0
            
            # Validar artigo
            if not self.validator.validar_artigo(artigo):
                logger.warning(f"⚠️ Artigo '{titulo}' não passou na validação")
                return 0
            
            logger.info(f"✅ Artigo encontrado: {artigo['title']}, extract length: {len(artigo.get('extract', ''))}, content length: {len(artigo.get('content', ''))}")
            
            # Usar LangChain para processamento
            logger.info(f"🔗 Processando com LangChain: {titulo}")
            documento = WikipediaDocument(
                title=artigo['title'],
                content=artigo['content'],
                url=artigo['url'],
                metadata={
                    'source': 'wikipedia_api',
                    'language': 'pt',
                    'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
            
            # Ingerir usando LangChain service
            chunks_criados = langchain_wikipedia_service.ingerir_documentos([documento],colecao=colecao)
            logger.info(f"✅ {chunks_criados} chunks criados com LangChain para '{titulo}'")
            
            # Registrar métrica
            self.metrics.record_article_processed(chunks_criados)
            
            # Também adicionar ao sistema legado para compatibilidade
            #chunks_legado = self._processar_e_armazenar_artigo(artigo, colecao=colecao)
            
            return chunks_criados
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar artigo '{titulo}': {e}")
            return 0
    
    def adicionar_artigos_com_langchain(self, titulos: List[str]) -> Dict[str, int]:
        """Adiciona múltiplos artigos usando pipeline LangChain"""
        try:
            logger.info(f"🔗 Processando {len(titulos)} artigos com LangChain")
            logger.info("📥#################################### Iniciando ingestão de múltiplos artigos com LangChain")
            
            documentos = []
            resultados = {}
            
            # Buscar todos os artigos
            for titulo in titulos:
                logger.info(f"📖 Buscando: {titulo}")
                artigo = self._buscar_artigo_wikipedia(titulo)
                
                if artigo:
                    documento = WikipediaDocument(
                        title=artigo['title'],
                        content=artigo['content'], 
                        url=artigo['url'],
                        metadata={
                            'source': 'wikipedia_api',
                            'language': 'pt',
                            'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    )
                    documentos.append(documento)
                    resultados[titulo] = 0  # Será atualizado depois
                else:
                    logger.warning(f"⚠️ Artigo não encontrado: {titulo}")
                    resultados[titulo] = 0
            
            try:
                if not self._initialized:
                    logger.error("❌ Serviço não inicializado")
                    raise Exception("Serviço não inicializado")
                # Buscar artigo na Wikipedia
                logger.info(f"📖 Buscando artigo: {titulo}")
                artigo = self._buscar_artigo_wikipedia(titulo)
                if not artigo:
                    logger.warning(f"⚠️ Artigo '{titulo}' não encontrado")
                    return 0
                # Validar artigo
                if not self.validator.validar_artigo(artigo):
                    logger.warning(f"⚠️ Artigo '{titulo}' não passou na validação")
                    return 0
                logger.info(f"✅ Artigo encontrado: {artigo['title']}, extract length: {len(artigo.get('extract', ''))}, content length: {len(artigo.get('content', ''))}")
                # Usar LangChain para processamento
                logger.info(f"🔗 Processando com LangChain: {titulo}")
                documento = WikipediaDocument(
                    title=artigo['title'],
                    content=artigo['content'],
                    url=artigo['url'],
                    metadata={
                        'source': 'wikipedia_api',
                        'language': 'pt',
                        'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                )
                # Patch: set LangChain service collection if provided
                selected_colecao = colecao if colecao else self.collection_name
                if hasattr(langchain_wikipedia_service, 'collection_name'):
                    langchain_wikipedia_service.collection_name = selected_colecao
                chunks_criados = langchain_wikipedia_service.ingerir_documentos([documento])
                logger.info(f"✅ {chunks_criados} chunks criados com LangChain para '{titulo}' na coleção '{selected_colecao}'")
                # Registrar métrica
                self.metrics.record_article_processed(chunks_criados)
                # Também adicionar ao sistema legado para compatibilidade
                chunks_legado = self._processar_e_armazenar_artigo(artigo, colecao=selected_colecao)
                return chunks_criados
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar artigo '{titulo}': {e}")
                return 0
            # Inserir no Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar chunk: {e}")
            return False
    
    def _buscar_artigo_wikipedia(self, titulo: str) -> Optional[Dict]:
        """Busca artigo na Wikipedia API com conteúdo completo - delegado ao WikipediaAPIClient"""
        return self.api_client.buscar_artigo_completo(titulo)
    
    def _processar_e_armazenar_artigo(self, artigo: Dict, colecao: str = None) -> int:
        """Processa artigo em chunks e armazena no Qdrant na coleção especificada"""
        if not self.client:
            return 0
        logger.info("📥#################################### Iniciando processamento de artigo para armazenamento legado")
        logger.info(f"COLEÇÃO: {colecao if colecao else self.collection_name} | TÍTULO: {artigo.get('title', 'Desconhecido')}")
        try:
            # Combinar extract e content
            texto_completo = f"{artigo.get('extract', '')} {artigo.get('content', '')}"
            # Dividir em chunks simples (por parágrafos)
            chunks = self._dividir_em_chunks(texto_completo)
            points = []
            collection_name = colecao if colecao else self.collection_name
            # Detectar dimensão do vetor da coleção
            try:
                collection_info = self.client.get_collection(collection_name)
                if hasattr(collection_info, 'vectors_config'):
                    vectors_config = collection_info.vectors_config
                    if isinstance(vectors_config, dict):
                        vector_dim = vectors_config.get('size', vectors_config.get('params', {}).get('size', 384))
                    else:
                        vector_dim = getattr(vectors_config, 'size', 384)
                else:
                    vector_dim = 384
            except Exception as e:
                logger.warning(f"Não foi possível detectar dimensão da coleção '{collection_name}', usando 384. Erro: {e}")
                vector_dim = 384
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Ignorar chunks muito pequenos
                    continue
                # Vetor fake com dimensão correta
                vector = [0.1] * int(vector_dim)
                # Gerar ID único como UUID
                point_id = str(uuid.uuid4())
                point = models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "title": artigo.get('title', ''),
                        "content": chunk,
                        "url": artigo.get('url', ''),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "description": artigo.get('description', ''),
                        "source": "wikipedia"
                    }
                )
                points.append(point)
            if points:
                try:
                    self.client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                except Exception as e:
                    logger.error(f"❌ Erro ao inserir pontos no Qdrant: {e}")
                    return 0
            return len(points)
        except Exception as e:
            logger.error(f"❌ Erro ao processar artigo: {e}")
            return 0
    

    def buscar_artigos(self, query: str, limit: int = 10,colecao: str = None) -> List[SearchResult]:
        """Busca artigos usando LangChain retriever e fallback para sistema legado"""
        try:
            logger.info("******** buscar_artigos ******************************************************")
            logger.info(f"🔍 Buscando por: '{query}' (limite: {limit}) na coleção {colecao}")
            
            # Primeiro: tentar busca com LangChain
            try:
                logger.info("🔗 Tentando busca com LangChain...")
                langchain_results = langchain_wikipedia_service.buscar_documentos(
                    query=query, 
                    limit=limit,
                    score_threshold=0.05,  # Threshold muito baixo para aceitar mais resultados
                    colecao=colecao 
                )
                
                if langchain_results:
                    logger.info(f"✅ LangChain encontrou {len(langchain_results)} resultados")
                    return langchain_results
                else:
                    logger.info("⚠️ LangChain não encontrou resultados, tentando sistema legado...")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro na busca LangChain: {e}, usando sistema legado...")
            
            # Fallback: usar sistema legado
            logger.info("🔄 Usando sistema de busca legado como fallback...")
            return self._buscar_artigos_legado(query, limit, colecao=colecao)
            
        except Exception as e:
            logger.error(f"❌ Erro geral na busca: {e}")
            return self._get_sample_results(query, limit)

    def _buscar_artigos_legado(self, query: str, limit: int = 10, colecao: str = None) -> List[SearchResult]:
        """Sistema de busca legado (backup) por coleção"""
        if not self.client:
            return self._get_sample_results(query, limit)
        try:
            collection_name = colecao if colecao else self.collection_name
            logger.info(f"🔍 Busca legado por: '{query}' (limite: {limit}) na coleção: {collection_name}")
            search_results = None
            query_terms = query.lower().split()
            try:
                search_results = self.client.scroll(
                    collection_name=collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="content",
                                match=models.MatchText(text=query)
                            )
                        ]
                    ),
                    limit=limit,
                    with_payload=True
                )
                logger.info(f"📝 Busca por content encontrou {len(search_results[0])} resultados")
            except Exception as e:
                logger.warning(f"⚠️ Erro na busca por content: {e}")
            if not search_results or len(search_results[0]) == 0:
                try:
                    search_results = self.client.scroll(
                        collection_name=collection_name,
                        scroll_filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="title",
                                    match=models.MatchText(text=query)
                                )
                            ]
                        ),
                        limit=limit,
                        with_payload=True
                    )
                    logger.info(f"📋 Busca por title encontrou {len(search_results[0])} resultados")
                except Exception as e:
                    logger.warning(f"⚠️ Erro na busca por title: {e}")
            if not search_results or len(search_results[0]) == 0:
                logger.info("🔄 Tentando busca manual em todos os documentos...")
                try:
                    all_results = self.client.scroll(
                        collection_name=collection_name,
                        limit=500,
                        with_payload=True
                    )
                    logger.info(f"📚 Encontrou {len(all_results[0])} documentos totais")
                    filtered_results = []
                    for hit in all_results[0]:
                        content = hit.payload.get("content", "").lower()
                        title = hit.payload.get("title", "").lower()
                        score = 0
                        for term in query_terms:
                            if term in title:
                                score += 3
                            if term in content:
                                score += 1
                        if score > 0:
                            filtered_results.append((hit, score))
                    filtered_results.sort(key=lambda x: x[1], reverse=True)
                    search_results = ([item[0] for item in filtered_results[:limit]], None)
                    logger.info(f"✅ Busca manual encontrou {len(search_results[0])} resultados relevantes")
                except Exception as e:
                    logger.error(f"❌ Erro na busca manual: {e}")
                    search_results = ([], None)
            artigo_dict = {}
            if search_results and len(search_results[0]) > 0:
                for hit in search_results[0]:
                    content = hit.payload.get("content", "")
                    title = hit.payload.get("title", "")
                    score = 0.5
                    for term in query_terms:
                        if term in title.lower():
                            score += 0.3
                        if term in content.lower():
                            score += 0.1
                    score = min(score, 1.0)
                    if title not in artigo_dict or score > artigo_dict[title].score:
                        artigo_dict[title] = SearchResult(
                            title=title,
                            content=content[:200] + ("..." if len(content) > 200 else ""),
                            url=hit.payload.get("url", ""),
                            score=score,
                            categories=[],
                            chunk_info={
                                "chunk_index": hit.payload.get("chunk_index", 0),
                                "total_chunks": hit.payload.get("total_chunks", 1),
                                "source": hit.payload.get("source", "unknown")
                            }
                        )
                resultados_unificados = list(artigo_dict.values())
                resultados_unificados = sorted(resultados_unificados, key=lambda x: x.score, reverse=True)[:limit]
                logger.info(f"✅ Retornando {len(resultados_unificados)} artigos reais unificados")
                return resultados_unificados
            results = []
            if search_results and len(search_results[0]) > 0:
                for hit in search_results[0]:
                    content = hit.payload.get("content", "").lower()
                    title = hit.payload.get("title", "").lower()
                    score = 0.5
                    for term in query_terms:
                        if term in title:
                            score += 0.3
                        if term in content:
                            score += 0.1
                    score = min(score, 1.0)
                    result = SearchResult(
                        title=hit.payload.get("title", ""),
                        content=hit.payload.get("content", ""),
                        url=hit.payload.get("url", ""),
                        score=score,
                        categories=[],
                        chunk_info={
                            "chunk_index": hit.payload.get("chunk_index", 0),
                            "total_chunks": hit.payload.get("total_chunks", 1),
                            "source": hit.payload.get("source", "unknown")
                        }
                    )
                    results.append(result)
                logger.info(f"✅ Retornando {len(results)} resultados reais")
                return results
            logger.warning("⚠️ Nenhum resultado encontrado, usando fallback")
            return self._get_sample_results(query, limit)
        except Exception as e:
            logger.error(f"❌ Erro geral na busca: {e}")
            return self._get_sample_results(query, limit)
    
    def buscar_para_rag(self, pergunta: str, max_chunks: int = 30, colecao: str = None) -> tuple[List[SearchResult], int, int, bool, dict]:
        """
        Executa apenas a busca semântica e retorna os resultados com telemetria.
        Retorna: (documentos, total_chunks, total_artigos, encontrou_resultados, telemetria_busca)
        """
        import time
        
        inicio_total = time.time()
        telemetria = {
            "tempo_embedding_ms": 0,
            "tempo_busca_qdrant_ms": 0,
            "tempo_processamento_ms": 0,
            "tempo_total_ms": 0,
            "query_length": len(pergunta),
            "max_chunks_solicitados": max_chunks
        }
        
        try:
            # Fase 1: Gerar embedding da query (simulado - LangChain faz internamente)
            inicio_busca = time.time()
            
            # Buscar documentos (inclui embedding + busca no Qdrant)
            documentos = self.buscar_artigos(pergunta, limit=max_chunks, colecao=colecao)
            
            tempo_busca = (time.time() - inicio_busca) * 1000
            telemetria["tempo_busca_qdrant_ms"] = round(tempo_busca, 2)
            
            # Fase 2: Processar resultados
            inicio_processamento = time.time()
            
            if not documentos or len(documentos) == 0:
                # Verificar se base está vazia
                if self.client:
                    try:
                        collection_info = self.client.get_collection(self.collection_name)
                        total_points = collection_info.points_count
                        
                        if total_points == 0:
                            logger.warning(f"⚠️ Base de conhecimento vazia!")
                            tempo_processamento = (time.time() - inicio_processamento) * 1000
                            telemetria["tempo_processamento_ms"] = round(tempo_processamento, 2)
                            telemetria["tempo_total_ms"] = round((time.time() - inicio_total) * 1000, 2)
                            return ([], 0, 0, False, telemetria)
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao verificar collection: {e}")
                
                logger.warning(f"⚠️ Nenhum artigo relevante encontrado")
                tempo_processamento = (time.time() - inicio_processamento) * 1000
                telemetria["tempo_processamento_ms"] = round(tempo_processamento, 2)
                telemetria["tempo_total_ms"] = round((time.time() - inicio_total) * 1000, 2)
                return ([], 0, 0, False, telemetria)
            
            # Calcular estatísticas
            total_chunks = len(documentos)
            artigos_unicos = set(doc.title for doc in documentos)
            total_artigos = len(artigos_unicos)
            
            tempo_processamento = (time.time() - inicio_processamento) * 1000
            telemetria["tempo_processamento_ms"] = round(tempo_processamento, 2)
            telemetria["tempo_total_ms"] = round((time.time() - inicio_total) * 1000, 2)
            telemetria["chunks_encontrados"] = total_chunks
            telemetria["artigos_encontrados"] = total_artigos
            
            logger.info(f"📊 Busca encontrou {total_chunks} chunks de {total_artigos} artigos em {telemetria['tempo_total_ms']}ms")
            
            return (documentos, total_chunks, total_artigos, True, telemetria)
            
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            telemetria["tempo_total_ms"] = round((time.time() - inicio_total) * 1000, 2)
            telemetria["erro"] = str(e)
            return ([], 0, 0, False, telemetria)
    
    async def perguntar_com_rag(self, pergunta: str, max_chunks: int = 3, colecao: str = None) -> RAGResponse:
        """Sistema RAG com Ollama, filtrando por coleção se fornecida"""
        start_time = time.time()
        start_time_str = datetime.datetime.fromtimestamp(start_time).strftime('%d/%m/%Y %H:%M:%S')
        await enviar_telemetria(f"Iniciando websocket... {start_time_str}")
        
        logger.info("///// perguntar_com_rag ///////////////////////////////////////////")
        logger.info(f"🤖 perguntar_com_rag '{pergunta}' (max_chunks={max_chunks}, colecao={colecao})")

        try:
            # ...aqui será implementada a detecção semântica de perguntas meta via embeddings...
            
            # Fase 1: Buscar documentos (SEMPRE buscar primeiro)
            search_start = time.time()
            await enviar_telemetria(f"Buscando artigos no Qdrant({colecao})")
            await asyncio.sleep(0.5)
            documentos = self.buscar_artigos(pergunta, limit=max_chunks, colecao=colecao)
            search_time = time.time() - search_start
            # Telemetria da busca semântica
            documentos, total_chunks, total_artigos, encontrou_resultados, telemetria_busca = self.buscar_para_rag(pergunta, max_chunks, colecao=colecao)
            
            # Log para debug
            if documentos:
                logger.warning(f"retornou {len(documentos)} docs: {[(d.title, round(d.score, 4)) for d in documentos]}")
                await enviar_telemetria(f" retornou {len(documentos)} documentos")
            else:
                logger.warning(f"🔍 buscar_artigos retornou 0 documentos")
                await enviar_telemetria("buscar_artigos retornou 0 documentos")
            
            await enviar_telemetria("Iniciando busca................")
            await asyncio.sleep(0.5)
            
            # Se não encontrou nada, verificar se é porque a base está vazia ou se realmente não tem o assunto
            if not documentos or len(documentos) == 0:
                try:
                    await enviar_telemetria("Não encontrou artigos na base")
                    if self.client:
                        collection_info = self.client.get_collection(self.collection_name)
                        total_points = collection_info.points_count
                        if total_points == 0:
                            logger.warning(f"⚠️ Base de conhecimento vazia!")
                            await enviar_telemetria("Não encontrou artigos na base")
                            return RAGResponse(
                                question=pergunta,
                                answer="A base de conhecimento está vazia. Por favor, adicione artigos através da interface web.",
                                sources=[],
                                reasoning="Base de conhecimento vazia",
                                model_info={"status": "base_vazia", "modelo": self.model_name}
                            )
                        else:
                            logger.warning(f"⚠️ Nenhum artigo relevante encontrado (base tem {total_points} documentos)")
                            await enviar_telemetria("Nenhum artigo relevante encontrado na base")
                            return RAGResponse(
                                question=pergunta,
                                answer="Não encontrei artigos sobre este assunto na base de conhecimento.",
                                sources=[],
                                reasoning=f"Sem artigos relevantes (base com {total_points} documentos)",
                                model_info={"status": "sem_artigos_relevantes", "modelo": self.model_name}
                            )
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao verificar collection: {e}")
                    await enviar_telemetria(f"Erro ao verificar collection: {e}")
                    return RAGResponse(
                        question=pergunta,
                        answer="Não encontrei artigos sobre este assunto na base de conhecimento.",
                        sources=[],
                        reasoning="Sem artigos relevantes",
                        model_info={"status": "sem_artigos", "modelo": self.model_name}
                    )
            
            # Verificar se há conteúdo suficiente na base
            try:
                await enviar_telemetria("Verificar se há conteúdo suficiente na base")
                await asyncio.sleep(0.5)
                if self.client:
                    collection_info = self.client.get_collection(self.collection_name)
                    total_points = collection_info.points_count
                    
                    # Threshold adaptativo baseado no tamanho da base (REDUZIDO para aceitar mais resultados)
                    if total_points < 10:
                        MIN_SIMILARITY_SCORE = 0.05  # 5% para bases muito pequenas (< 10 docs)
                        logger.info(f"📊 Base pequena ({total_points} chunks) - usando threshold {MIN_SIMILARITY_SCORE}")
                    elif total_points < 50:
                        MIN_SIMILARITY_SCORE = 0.08  # 8% para bases pequenas (10-50 docs)
                        logger.info(f"📊 Base média ({total_points} chunks) - usando threshold {MIN_SIMILARITY_SCORE}")
                    else:
                        MIN_SIMILARITY_SCORE = 0.12  # 12% para bases grandes (50+ docs)
                        logger.info(f"📊 Base grande ({total_points} chunks) - usando threshold {MIN_SIMILARITY_SCORE}")
                else:
                    MIN_SIMILARITY_SCORE = 0.08
            except Exception as e:
                MIN_SIMILARITY_SCORE = 0.08
                logger.warning(f"Erro ao verificar tamanho da base: {e}")
            
            # Estratégia 1: Aplicar boosting para matches exatos no título ANTES de filtrar
            await asyncio.sleep(0.5)
            import re
            stopwords = ['o', 'que', 'é', 'a', 'de', 'da', 'do', 'um', 'uma', 'os', 'as', 'para', 'com', 'por']
            termos_pergunta = [re.sub(r'[^w\s]', '', t.lower()) for t in pergunta.split() if t.lower() not in stopwords]
            termos_pergunta = [t for t in termos_pergunta if len(t) > 2]  # Filtrar termos muito curtos
            # Se não sobrou nenhum termo, tenta pegar a última palavra relevante (ex: 'Jakarta' em 'o que é Jakarta?')
            if not termos_pergunta:
                palavras = [re.sub(r'[^w\s]', '', t.lower()) for t in pergunta.split() if t.lower() not in stopwords]
                palavras = [t for t in palavras if t]
                if palavras:
                    termos_pergunta = [palavras[-1]]
            # Aplicar boosting de 3x para matches exatos no título
            titulos_pergunta = [t for t in termos_pergunta]
            for doc in documentos:
                titulo_lower = doc.title.lower()
                # Se algum termo da pergunta é exatamente o título
                if any(titulo_lower == termo for termo in titulos_pergunta):
                    doc.score = doc.score * 3.0
                    doc._force_include = True  # Marcar para inclusão forçada
                    logger.info(f"🚀 Boosting aplicado: '{doc.title}' - score {doc.score/3.0:.4f} → {doc.score:.4f}")
            # Reordenar documentos após boosting
            documentos = sorted(documentos, key=lambda x: x.score, reverse=True)
            # Filtrar por score mínimo de similaridade OU inclusão forçada
            documentos_relevantes = [doc for doc in documentos if doc.score >= MIN_SIMILARITY_SCORE or getattr(doc, '_force_include', False)]
            logger.warning(f"📊 Após filtro de score ({MIN_SIMILARITY_SCORE}): {len(documentos_relevantes)} docs - {[(d.title, round(d.score, 4)) for d in documentos_relevantes]}")
            
            # Estratégia 2: Verificar se termos da pergunta aparecem no título ou conteúdo
            # SEMPRE verificar termos exatos para evitar respostas inventadas
            if documentos_relevantes:
                # Extrair termos principais da pergunta (remover palavras comuns e caracteres especiais)
                import re
                import unicodedata
                
                await enviar_telemetria("Extrair termos principais da pergunta (remover palavras comuns e caracteres especiais")
                await asyncio.sleep(0.5)

                def normalizar_texto(texto):
                    """Remove acentos e normaliza texto para comparação"""
                    # Normalizar unicode (NFD = decompor caracteres com acentos)
                    texto_nfd = unicodedata.normalize('NFD', texto)
                    # Remover marcas diacríticas (acentos)
                    texto_sem_acento = ''.join(c for c in texto_nfd if unicodedata.category(c) != 'Mn')
                    return texto_sem_acento.lower()
                
                stopwords = ['o', 'que', 'é', 'a', 'de', 'da', 'do', 'um', 'uma', 'os', 'as', 'para', 'com', 'por', 'onde', 'fica', 'qual', 'sobre', 'sabe', 'vc', 'você', 'me', 'diz', 'fala']
                # Remover pontuação e caracteres especiais, manter apenas letras e números
                termos_pergunta = [re.sub(r'[^\w\s]', '', t.lower()) for t in pergunta.split() if t.lower() not in stopwords]
                termos_pergunta = [t for t in termos_pergunta if len(t) > 2]  # Filtrar termos muito curtos
                
                if not termos_pergunta:
                    # Se não há termos válidos, aceitar os documentos com score alto
                    logger.info("⚠️ Nenhum termo válido extraído da pergunta, usando apenas scores")
                else:
                    # Verificar se pelo menos um termo aparece no título ou conteúdo
                    docs_com_termo_exato = []
                    docs_score_alto = []  # Documentos com score alto mesmo sem match exato
                    logger.warning(f"🔄 Iniciando verificação de {len(documentos_relevantes)} documentos")
                    for doc in documentos_relevantes:
                        logger.warning(f"  🔎 Verificando documento: '{doc.title}' (score: {doc.score})")
                        titulo_normalizado = normalizar_texto(doc.title)
                        conteudo_normalizado = normalizar_texto(doc.content)
                        
                        # Verificar com word boundaries para evitar falsos positivos
                        tem_termo = False
                        for termo in termos_pergunta:
                            termo_normalizado = normalizar_texto(termo)
                            # Usar word boundaries (\b) para matches exatos de palavras
                            pattern = r'\b' + re.escape(termo_normalizado) + r'\b'
                            if re.search(pattern, titulo_normalizado) or re.search(pattern, conteudo_normalizado):
                                tem_termo = True
                                break
                        
                        # Verificação adicional: se título aparece na pergunta (match reverso)
                        titulo_palavras = [p for p in titulo_normalizado.split() if len(p) > 2]
                        pergunta_normalizada = normalizar_texto(pergunta)
                        titulo_na_pergunta = any(palavra in pergunta_normalizada for palavra in titulo_palavras)
                        
                        if tem_termo or titulo_na_pergunta:
                            docs_com_termo_exato.append(doc)
                            razao = "termos" if tem_termo else "título na pergunta"
                            logger.warning(f"✅ Documento '{doc.title}' aceito ({razao}): {termos_pergunta}")
                        elif doc.score > 0.60:  # Score MUITO alto (60%+), aceitar mesmo sem match exato
                            docs_score_alto.append(doc)
                            logger.warning(f"✅ Documento '{doc.title}' aceito (score muito alto: {doc.score:.4f})")
                        else:
                            logger.warning(f"⚠️ Documento '{doc.title}' não contém termos da pergunta {termos_pergunta} (score: {doc.score})")
                    
                    # Estratégia 3: Combinar documentos com termo exato + scores altos
                    # Priorizar docs com termo exato, mas incluir todos os relevantes
                    documentos_relevantes = docs_com_termo_exato + docs_score_alto
                    
                    # Se não encontrou NENHUM documento com termo exato E não há scores muito altos, rejeitar
                    if not docs_com_termo_exato and not docs_score_alto:
                        logger.warning(f"⚠️ Nenhum documento relevante para '{pergunta}' (termos: {termos_pergunta}, sem scores altos)")
                        return RAGResponse(
                            question=pergunta,
                            answer="Ainda não existem artigos sobre este assunto na base de conhecimento.",
                            sources=[],
                            reasoning="Sem artigos relevantes para a pergunta (sem matches de termo e scores baixos)",
                            model_info={"status": "no_match", "model": self.model_name}
                        )
            
            if not documentos_relevantes:
                logger.warning(f"⚠️ Nenhum artigo com similaridade suficiente para: {pergunta} (scores: {[doc.score for doc in documentos]})")
                return RAGResponse(
                    question=pergunta,
                    answer="Ainda não existem artigos sobre este assunto na base de conhecimento.",
                    sources=[],
                    reasoning="Sem artigos relevantes com similaridade suficiente",
                    model_info={"status": "baixa_similaridade", "modelo": self.model_name}
                )
            
            # NÃO remover duplicatas - permitir múltiplos chunks do mesmo artigo
            # Isso é crucial para queries técnicas onde informação específica pode estar em chunks diferentes
            documentos = documentos_relevantes
            
            logger.info(f"📚 Encontrou {len(documentos)} chunks para RAG (artigos: {list(set([d.title for d in documentos]))})")
            await enviar_telemetria("Gerando resposta com Ollama. Isso pode demorar.....")
            await asyncio.sleep(0.5)
            
            # OTIMIZAÇÃO 1: Limitar número de chunks (máximo 6 - balanceado)
            # Priorizar chunks mais relevantes (já vêm ordenados por score)
            documentos_limitados = documentos[:6]  # Máximo 6 chunks (aumentado de 3)
            if len(documentos) > 6:
                logger.info(f"⚡ Limitando de {len(documentos)} para 6 chunks mais relevantes")
            

            
            # OTIMIZAÇÃO 2: Chunks de tamanho médio (250 chars)
            context_parts = []
            for i, doc in enumerate(documentos_limitados, 1):
                # Balanceamento: mais contexto, mas ainda rápido
                content_snippet = doc.content[:500]  # Aumentado para 500 para respostas mais completas
                if len(doc.content) > 250:
                    content_snippet += "..."
                
                context_parts.append(f"[{i}] {doc.title}:\n{content_snippet}")
            
            context = "\n\n".join(context_parts)
            logger.info(f"📝 Contexto preparado com {len(context)} caracteres de {len(documentos_limitados)} fontes")
            
            # Fase 2: Gerar resposta com Ollama
            logger.info(f"🤖 Chamando Ollama com modelo {self.model_name}...")
            generation_start = time.time()
            
            resposta, telemetria_llm = self._generate_answer_with_ollama(pergunta, context)
            generation_time = time.time() - generation_start
            total_time = time.time() - start_time

            await enviar_telemetria("Resposta com Ollama recebida!")
            await asyncio.sleep(0.5)
            await enviar_telemetria(f"Processando rede... ({round(generation_time,2)}s)")
            await asyncio.sleep(0.5)
            await enviar_telemetria(f"Gerando resposta... ({round(generation_time-0.82,2)}s)")
            await asyncio.sleep(0.5)
            
            # Calcular estatísticas
            total_chunks = len(documentos)
            artigos_unicos = set(doc.title for doc in documentos)
            total_artigos = len(artigos_unicos)
            
            logger.info(f"📊 Estatísticas - {total_chunks} chunks de {total_artigos} artigos únicos")
            logger.info(f"⏱️ Tempos - Busca: {search_time:.2f}s, Geração: {generation_time:.2f}s, Total: {total_time:.2f}s")
            
            # Montar telemetria detalhada no formato esperado pelo frontend
            telemetria = {
                "tempo_total_ms": round(total_time * 1000, 2),
                "tempo_busca_qdrant_ms": round(search_time * 1000, 2),
                "tempo_filtragem_ms": telemetria_busca.get("tempo_filtragem_ms", 0),
                "resultados_antes_filtro": telemetria_busca.get("resultados_antes_filtro", total_chunks),
                "resultados_depois_filtro": len(documentos),
                # Campos extras
                "chunks_encontrados": total_chunks,
                "artigos_encontrados": total_artigos,
                # LLM
                "llm": telemetria_llm,
                "sucesso": "Verdadeiro" if total_chunks > 0 else "Falso"
            }

            await enviar_telemetria("Finalizando...")
            await asyncio.sleep(0.5)
            
            return RAGResponse(
                question=pergunta,
                answer=resposta,
                sources=documentos,
                reasoning=f"Resposta gerada com {self.model_name} baseada em {total_chunks} chunks de {total_artigos} artigos",
                model_info={
                    "status": "ok", 
                    "modelo": self.model_name,
                    "tempos": {
                        "busca": round(search_time, 2),
                        "geracao": round(generation_time, 2),
                        "total": round(total_time, 2)
                    }
                },
                total_chunks=total_chunks,
                total_artigos=total_artigos,
                telemetria=telemetria
            )
            
        except Exception as e:
            logger.error(f"❌ Erro no RAG: {e}", exc_info=True)  # exc_info=True mostra traceback completo
            return RAGResponse(
                question=pergunta,
                answer=f"Erro ao processar a pergunta: {str(e)}",
                sources=[],
                reasoning=f"Erro técnico: {str(e)}",
                model_info={"status": "erro", "modelo": "nenhum", "erro": str(e)}
            )
    
    def _generate_answer_with_ollama(self, question: str, context: str) -> str:
        """Gera resposta usando Ollama"""
        total_start = time.time()
        
        # OTIMIZAÇÃO 3: Contexto balanceado (1200 chars)
        max_context_length = 3000  # Aumentado para 3000 para permitir mais contexto
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."
            logger.info(f"📝 Contexto truncado para {max_context_length} caracteres")
        
        prompt_build_start = time.time()
        # OTIMIZAÇÃO 4: Prompt MUITO mais curto para reduzir tokens (895→~300)
        # Prompt sempre força resposta em português e limita o conhecimento ao contexto fornecido
        prompt = (
            f"""Responda em português usando SOMENTE as informações abaixo extraídas dos artigos cadastrados na base de conhecimento. 
               NÃO utilize nenhum conhecimento externo, não invente fatos e não faça suposições. Se não encontrar a resposta nos textos fornecidos, 
               responda apenas: 'Não encontrei informações nos artigos cadastrados. Mas verifique todos artigos.'\n\n"
            f"Contexto dos artigos:\n\n{context}\n\nPergunta: {question}"""
        )
        prompt_build_time = time.time() - prompt_build_start

        logger.info(f"🤖 Enviando prompt para Ollama (tamanho: {len(prompt)} caracteres)")
        logger.info(f"⏱️ Tempo de preparação do prompt: {prompt_build_time*1000:.1f}ms")
        
        url = f"http://{self.ollama_host}:{self.ollama_port}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.6,
                "num_predict": 400,      # Aumentado para 400 tokens (respostas mais completas)
                "num_ctx": 1536,         # Aumentado: 1024→1536 (meio termo)
                "repeat_penalty": 1.1,
                "top_k": 40,
                "stop": ["Pergunta:", "\n\n\n", "\n\nRegras:"]
            }
        }
        
        logger.info(f"⏱️ Aguardando resposta do Ollama (modelo: {self.model_name}, timeout: 600s)...")
        logger.info(f"⚙️ Config: temp={payload['options']['temperature']}, num_predict={payload['options']['num_predict']}, num_ctx={payload['options']['num_ctx']}")
        
        request_start = time.time()
        
        try:
            response = requests.post(url, json=payload, timeout=600)
            request_time = time.time() - request_start
            
            logger.info(f"📡 Ollama respondeu com status {response.status_code} em {request_time:.1f}s")
            
            if response.status_code == 200:
                parse_start = time.time()
                data = response.json()
                answer = data.get('response', 'Erro ao gerar resposta').strip()
                parse_time = time.time() - parse_start
                
                total_time = time.time() - total_start
                
                # Estatísticas detalhadas do Ollama (se disponíveis)
                eval_count = data.get('eval_count', 0)
                eval_duration = data.get('eval_duration', 0) / 1e9 if data.get('eval_duration') else 0
                prompt_eval_count = data.get('prompt_eval_count', 0)
                prompt_eval_duration = data.get('prompt_eval_duration', 0) / 1e9 if data.get('prompt_eval_duration') else 0
                
                # Criar telemetria estruturada
                telemetria = {
                    "prompt_tokens": prompt_eval_count,
                    "prompt_eval_time": round(prompt_eval_duration, 2),
                    "prompt_tokens_per_sec": round(prompt_eval_count / prompt_eval_duration, 1) if prompt_eval_duration > 0 else 0,
                    "completion_tokens": eval_count,
                    "completion_time": round(eval_duration, 2),
                    "completion_tokens_per_sec": round(eval_count / eval_duration, 1) if eval_duration > 0 else 0,
                    "total_tokens": prompt_eval_count + eval_count,
                    "total_time": round(request_time, 2),
                    "model": self.model_name,
                    "config": {
                        "temperature": 0.6,
                        "num_predict": 150,
                        "num_ctx": 1536
                    }
                }
                
                logger.info(f"✅ Resposta gerada em {request_time:.1f}s (tamanho: {len(answer)} caracteres)")
                logger.info(f"📊 BREAKDOWN DETALHADO:")
                logger.info(f"   └─ Preparação prompt: {prompt_build_time*1000:.1f}ms")
                logger.info(f"   └─ Rede/Processamento: {request_time:.2f}s")
                if prompt_eval_count > 0:
                    logger.info(f"      ├─ Avaliação do prompt: {prompt_eval_duration:.2f}s ({prompt_eval_count} tokens, {prompt_eval_count/prompt_eval_duration:.0f} tok/s)")
                if eval_count > 0:
                    logger.info(f"      └─ Geração da resposta: {eval_duration:.2f}s ({eval_count} tokens, {eval_count/eval_duration:.0f} tok/s)")
                logger.info(f"   └─ Parse JSON: {parse_time*1000:.1f}ms")
                logger.info(f"   └─ Total _generate_answer: {total_time:.2f}s")
                
                return answer, telemetria
            else:
                error_text = response.text[:200] if response.text else "sem detalhes"
                logger.error(f"❌ Ollama erro {response.status_code}: {error_text}")
                return f"Erro: LLM respondeu com status {response.status_code}", {}
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Timeout ao gerar resposta (>600s)")
            return "Timeout: A pergunta demorou muito para ser processada. Tente ser mais específico.", {}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"🔌 Erro de conexão com Ollama: {e}")
            return "Erro: Não foi possível conectar ao serviço de LLM.", {}
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao chamar Ollama: {e}", exc_info=True)
            return f"Erro ao gerar resposta: {str(e)}", {}
    
    def _get_sample_results(self, query: str, limit: int) -> List[SearchResult]:
        """Retorna lista vazia - não usar samples hardcoded"""
        logger.warning(f"⚠️ Nenhum resultado encontrado para '{query}' - retornando lista vazia")
        return []
    
    def obter_estatisticas(self, colecao=None) -> Dict[str, Any]:
        """Estatísticas da base Wikipedia ou coleção escolhida"""
        try:
            collection_name = colecao if colecao else self.collection_name
            if self.client:
                collection_info = self.client.get_collection(collection_name)
                # Buscar número de artigos únicos
                all_points = []
                offset = None
                while True:
                    result = self.client.scroll(
                        collection_name=collection_name,
                        limit=100,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False
                    )
                    points, offset = result
                    all_points.extend(points)
                    if offset is None:
                        break
                artigos_dict = {}
                for point in all_points:
                    title = point.payload.get('title', 'Sem título')
                    artigos_dict[title] = True
                total_artigos = len(artigos_dict)
                return {
                    "sistema_offline": True,
                    "colecao": collection_name,
                    "total_chunks": collection_info.points_count,
                    "total_artigos": total_artigos,
                    "dimensoes_vetor": collection_info.config.params.vectors.size,
                    "distancia": collection_info.config.params.vectors.distance.value,
                    "modelo_llm": self.model_name,
                    "status": "funcional"
                }
            else:
                return {
                    "sistema_offline": True,
                    "colecao": "nao_conectado",
                    "total_chunks": 0,
                    "total_artigos": 0,
                    "status": "modo_exemplo"
                }
        except Exception as e:
            return {"erro": f"Erro ao obter estatísticas: {str(e)}"}
    
    def listar_todos_artigos(self, colecao=None) -> Dict[str, Any]:
        """Lista todos os artigos únicos na base de conhecimento, filtrando por coleção se fornecida"""
        try:
            if not self.client:
                logger.error("❌ Cliente Qdrant não inicializado")
                return {"artigos": [], "total": 0}

            # Usar coleção fornecida ou padrão
            collection_name = colecao if colecao else "wikipedia_langchain"
            all_points = []
            offset = None
            while True:
                result = self.client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, offset = result
                all_points.extend(points)
                
                if offset is None:
                    break
            
            # Agrupar por título e pegar informações únicas
            artigos_dict = {}
            for point in all_points:
                title = point.payload.get('title', 'Sem título')
                if title not in artigos_dict:
                    artigos_dict[title] = {
                        'title': title,
                        'url': point.payload.get('url', ''),
                        'chunks': 0,
                        'timestamp': point.payload.get('timestamp', ''),
                        'preview': point.payload.get('content', '')[:200]
                    }
                artigos_dict[title]['chunks'] += 1
            
            # Converter para lista e ordenar por título
            artigos_list = sorted(artigos_dict.values(), key=lambda x: x['title'].lower())
            
            logger.info(f"📚 Encontrados {len(artigos_list)} artigos únicos ({len(all_points)} chunks total)")
            
            return {
                "artigos": artigos_list,
                "total": len(artigos_list),
                "total_chunks": len(all_points)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar artigos: {e}")
            return {"artigos": [], "total": 0, "erro": str(e)}
    
    def limpar_colecao(self) -> bool:
        """Remove todos os pontos da coleção"""
        try:
            if not self.client:
                logger.error("❌ Cliente Qdrant não inicializado")
                return False
                
            # Deletar e recriar a coleção
            try:
                self.client.delete_collection(self.collection_name)
                logger.info(f"🗑️ Coleção {self.collection_name} removida")
            except Exception:
                logger.info(f"⚠️ Coleção {self.collection_name} não existia")
            
            # Recriar coleção vazia
            self._criar_colecao(self)
            logger.info(f"✅ Coleção {self.collection_name} recriada vazia")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar coleção: {e}")
            return False
    
    def _processar_lote_chunks(self, chunk_batch: List[Dict]) -> int:
        """Processa um lote de chunks de dumps"""
        if not self.client or not chunk_batch:
            return 0
            
        try:
            points = []
            
            for chunk_data in chunk_batch:
                # TODO: Gerar embedding real aqui
                # Para simplificar, usar vetor fake (em produção seria embeddings reais)
                fake_vector = [0.1] * 384
                
                point_id = str(uuid.uuid4())
                
                point = models.PointStruct(
                    id=point_id,
                    vector=fake_vector,
                    payload={
                        "title": chunk_data['title'],
                        "content": chunk_data['content'], 
                        "url": chunk_data['url'],
                        "chunk_index": chunk_data.get('chunk_index', 0),
                        "total_chunks": chunk_data.get('total_chunks', 1),
                        "article_id": chunk_data.get('article_id', 0),
                        "timestamp": chunk_data.get('timestamp', ''),
                        "source": chunk_data.get('source', 'wikipedia_dump')
                    }
                )
                points.append(point)
            
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"✅ Lote processado: {len(points)} chunks adicionados")
            
            return len(points)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar lote: {e}")
            return 0
    
    def verificar_status(self, colecao=None) -> Dict[str, Any]:
        """Status completo do sistema, opcionalmente para uma coleção específica"""
        # Verifica número de coleções no Qdrant
        colecoes_count = 0
        colecoes_lista = []
        collection_name = colecao if colecao else self.collection_name
        if self.client:
            try:
                colecoes_obj = self.client.get_collections()
                colecoes_count = len(colecoes_obj.collections)
                colecoes_lista = [col.name for col in colecoes_obj.collections]
            except Exception:
                colecoes_count = 0
                colecoes_lista = []

        # Campos obrigatórios do modelo StatusResponse
        # Verificar status do Ollama
        ollama_disponivel = False
        modelo_llm = getattr(self, 'model_name', 'unknown')
        try:
            url = f"http://{getattr(self, 'ollama_host', 'localhost')}:{getattr(self, 'ollama_port', 11434)}/api/version"
            import requests
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                ollama_disponivel = True
        except Exception:
            ollama_disponivel = False

        # Se quiser retornar status da coleção específica, pode customizar aqui
        return {
            "status": "ok" if self._initialized else "error",
            "qdrant_conectado": self.client is not None,
            "colecao": collection_name,
            "colecoes": colecoes_count,
            "colecoes_lista": colecoes_lista,
            "modelo_embedding_carregado": True,  # ajuste conforme lógica real
            "modelo_embedding_nome": self.embedding_model_name,
            "text_splitter_configurado": True,    # ajuste conforme lógica real
            "openai_configurado": False,
            "inicializado": self._initialized,
            "ollama_disponivel": ollama_disponivel,
            "modelo_llm": modelo_llm
        }
    
    def obter_metricas(self) -> Dict:
        """Retorna métricas coletadas pelo serviço"""
        return self.metrics.get_metrics()
    
    def resetar_metricas(self):
        """Reseta todas as métricas coletadas"""
        self.metrics.reset_metrics()
    
    def _test_ollama_connection(self) -> bool:
        """Testa se Ollama está respondendo"""
        try:
            url = f"http://{self.ollama_host}:{self.ollama_port}/api/version"
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            return False


# Instância global do serviço
wikipedia_offline_service = WikipediaOfflineService()