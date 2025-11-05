"""
Offline Wikipedia RAG Service

Serviço principal que integra:
- Processamento de dumps XML da Wikipedia
- LLM local (Ollama/Transformers)
- Pipeline LangChain completo
- Sistema RAG offline

Este serviço substitui o wikipediaService.py original para funcionar completamente offline.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_core.documents import Document

from .xmlWikipediaProcessor import OfflineWikipediaRAG, WikipediaArticle
from .localLLMService import LocalLLMService, LLMConfig

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Resultado de busca offline"""
    title: str
    content: str
    url: str
    score: float
    categories: List[str]
    chunk_info: Dict[str, Any]


@dataclass
class RAGResponse:
    """Resposta do sistema RAG offline"""
    question: str
    answer: str
    sources: List[SearchResult]
    reasoning: str
    model_info: Dict[str, str]


class OfflineWikipediaService:
    """Serviço principal para Wikipedia offline com RAG"""
    
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.local_llm = None
        self.offline_rag = None
        self.collection_name = "wikipedia_offline"
        self._initialized = False
        
    def inicializar(self):
        """Inicializa todos os componentes do sistema offline"""
        if self._initialized:
            return
            
        logger.info("🚀 Inicializando Wikipedia Offline RAG Service...")
        
        try:
            self._conectar_qdrant()
            self._carregar_modelo_embedding()
            self._inicializar_llm_local()
            self._configurar_offline_rag()
            
            # Verificar se há dados na coleção
            self._verificar_dados_existentes()
            
            self._initialized = True
            logger.info("✅ Wikipedia Offline RAG Service inicializado!")
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            raise
    
    def _conectar_qdrant(self):
        """Estabelece conexão com Qdrant"""
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        
        max_retries = 30
        for attempt in range(max_retries):
            try:
                self.client = QdrantClient(host=host, port=port)
                self.client.get_collections()
                logger.info(f"✅ Conectado ao Qdrant em {host}:{port}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Aguardando Qdrant... Tentativa {attempt + 1}/{max_retries}")
                    time.sleep(2)
                else:
                    raise Exception(f"❌ Erro ao conectar com Qdrant após {max_retries} tentativas: {e}")
    
    def _carregar_modelo_embedding(self):
        """Carrega modelo de embeddings"""
        model_name = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        logger.info(f"📚 Carregando modelo de embeddings: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        logger.info("✅ Modelo de embeddings carregado")
    
    def _inicializar_llm_local(self):
        """Inicializa LLM local"""
        logger.info("🤖 Inicializando LLM local...")
        
        # Configuração do LLM
        llm_config = LLMConfig(
            model_type=os.getenv("LLM_TYPE", "ollama"),
            model_name=os.getenv("LLM_MODEL", "phi3:mini"),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "512")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3"))
        )
        
        self.local_llm = LocalLLMService(llm_config)
        self.local_llm.initialize()
        
        logger.info("✅ LLM local inicializado")
    
    def _configurar_offline_rag(self):
        """Configura sistema RAG offline"""
        data_dir = os.getenv("DATA_DIR", "data")
        self.offline_rag = OfflineWikipediaRAG(data_dir, self.collection_name)
        self.offline_rag.client = self.client
        self.offline_rag.embedding_model = self.embedding_model
    
    def _verificar_dados_existentes(self):
        """Verifica se já existem dados na coleção"""
        try:
            collections = self.client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)
            
            if collection_exists:
                collection_info = self.client.get_collection(self.collection_name)
                if collection_info.points_count > 0:
                    logger.info(f"✅ Coleção existente com {collection_info.points_count} documentos")
                    return
            
            logger.warning("⚠️ Nenhum dado encontrado. Use ingest_wikipedia() para carregar dados.")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar dados existentes: {e}")
    
    def ingest_wikipedia(self, max_articles: int = 1000):
        """Executa ingestão completa da Wikipedia"""
        if not self._initialized:
            raise Exception("Serviço não foi inicializado")
        
        logger.info(f"📥 Iniciando ingestão de {max_articles} artigos da Wikipedia...")
        
        try:
            self.offline_rag.ingest_wikipedia_dump(max_articles)
            logger.info("✅ Ingestão da Wikipedia concluída!")
            
        except Exception as e:
            logger.error(f"❌ Erro na ingestão: {e}")
            raise
    
    def buscar_artigos(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Busca semântica em artigos offline"""
        if not self._initialized:
            raise Exception("Serviço não foi inicializado")
        
        try:
            # Gerar embedding da query
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Buscar no Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Converter para SearchResult
            results = []
            for hit in search_results:
                result = SearchResult(
                    title=hit.payload.get("title", ""),
                    content=hit.payload.get("content", ""),
                    url=hit.payload.get("url", ""),
                    score=hit.score,
                    categories=hit.payload.get("categories", []),
                    chunk_info={
                        "chunk_index": hit.payload.get("chunk_index", 0),
                        "total_chunks": hit.payload.get("total_chunks", 1),
                        "chunk_id": hit.payload.get("chunk_id", ""),
                        "wikipedia_id": hit.payload.get("wikipedia_id", "")
                    }
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []
    
    def perguntar_com_rag(self, pergunta: str, max_chunks: int = 5) -> RAGResponse:
        """Sistema RAG completo offline"""
        if not self._initialized:
            raise Exception("Serviço não foi inicializado")
        
        try:
            # 1. Buscar documentos relevantes
            documentos_relevantes = self.buscar_artigos(pergunta, limit=max_chunks)
            
            if not documentos_relevantes:
                return RAGResponse(
                    question=pergunta,
                    answer="Desculpe, não encontrei informações relevantes para responder sua pergunta na base de conhecimento local.",
                    sources=[],
                    reasoning="Nenhum documento relevante foi encontrado na base offline.",
                    model_info=self.local_llm.get_status()
                )
            
            # 2. Preparar contexto
            context_parts = []
            for i, doc in enumerate(documentos_relevantes):
                context_parts.append(f"[Fonte {i+1}: {doc.title}]\n{doc.content[:800]}...")
            
            context = "\n\n".join(context_parts)
            
            # 3. Gerar resposta com LLM local
            resposta = self.local_llm.generate_response(context, pergunta)
            
            return RAGResponse(
                question=pergunta,
                answer=resposta,
                sources=documentos_relevantes,
                reasoning=f"Resposta gerada offline baseada em {len(documentos_relevantes)} fontes locais da Wikipedia.",
                model_info=self.local_llm.get_status()
            )
            
        except Exception as e:
            logger.error(f"Erro no RAG: {e}")
            return RAGResponse(
                question=pergunta,
                answer=f"Erro ao processar pergunta offline: {str(e)}",
                sources=[],
                reasoning=f"Erro técnico no sistema offline: {str(e)}",
                model_info={}
            )
    
    def adicionar_artigos_xml(self, xml_path: str, max_articles: int = 100) -> int:
        """Adiciona artigos de um arquivo XML específico"""
        if not self._initialized:
            raise Exception("Serviço não foi inicializado")
        
        try:
            from .xmlWikipediaProcessor import WikipediaXMLProcessor
            
            processor = WikipediaXMLProcessor()
            xml_file = Path(xml_path)
            
            if not xml_file.exists():
                raise FileNotFoundError(f"Arquivo XML não encontrado: {xml_path}")
            
            # Processar artigos
            articles = []
            for i, article in enumerate(processor.process_dump(xml_file)):
                articles.append(article)
                if i >= max_articles - 1:
                    break
            
            if not articles:
                logger.warning("Nenhum artigo encontrado no arquivo XML")
                return 0
            
            # Criar documentos LangChain
            documents = processor.create_langchain_documents(articles)
            
            # Armazenar no Qdrant
            self.offline_rag._store_documents(documents)
            
            logger.info(f"✅ {len(articles)} artigos adicionados do arquivo XML")
            return len(articles)
            
        except Exception as e:
            logger.error(f"Erro ao adicionar artigos XML: {e}")
            raise
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Estatísticas completas do sistema offline"""
        if not self._initialized:
            raise Exception("Serviço não foi inicializado")
        
        try:
            # Estatísticas do Qdrant
            collection_info = self.client.get_collection(self.collection_name)
            
            # Contar artigos únicos
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000
            )
            
            artigos_unicos = set()
            if scroll_result[0]:
                for point in scroll_result[0]:
                    title = point.payload.get("title", "")
                    if title:
                        artigos_unicos.add(title)
            
            # Status do LLM
            llm_status = self.local_llm.get_status() if self.local_llm else {}
            
            return {
                "nome_colecao": self.collection_name,
                "total_chunks": collection_info.points_count,
                "artigos_unicos": len(artigos_unicos),
                "dimensoes_vetor": collection_info.config.params.vectors.size,
                "distancia": collection_info.config.params.vectors.distance.value,
                "sistema_offline": True,
                "llm_local": llm_status,
                "modelo_embedding": self.embedding_model.get_sentence_embedding_dimension() if self.embedding_model else 0,
                "data_dir": getattr(self.offline_rag, 'data_dir', 'N/A') if self.offline_rag else 'N/A'
            }
            
        except Exception as e:
            return {"erro": f"Erro ao obter estatísticas: {str(e)}"}
    
    def verificar_status(self) -> Dict[str, Any]:
        """Status completo do sistema offline"""
        try:
            collections = self.client.get_collections() if self.client else None
            llm_status = self.local_llm.get_status() if self.local_llm else {}
            
            return {
                "status": "ok" if self._initialized else "error",
                "sistema_offline": True,
                "qdrant_conectado": self.client is not None,
                "colecoes": len(collections.collections) if collections else 0,
                "modelo_embedding_carregado": self.embedding_model is not None,
                "llm_local_status": llm_status,
                "offline_rag_configurado": self.offline_rag is not None,
                "inicializado": self._initialized,
                "componentes": {
                    "qdrant": self.client is not None,
                    "embeddings": self.embedding_model is not None,
                    "llm_local": self.local_llm is not None and self.local_llm.llm is not None,
                    "offline_rag": self.offline_rag is not None
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "erro": str(e),
                "sistema_offline": True,
                "inicializado": False
            }
    
    def listar_modelos_disponiveis(self) -> Dict[str, Any]:
        """Lista modelos LLM disponíveis"""
        if not self.local_llm:
            return {"erro": "LLM local não inicializado"}
        
        return self.local_llm.get_status()
    
    def configurar_llm(self, model_type: str, model_name: str) -> bool:
        """Reconfigura o LLM local"""
        try:
            config = LLMConfig(
                model_type=model_type,
                model_name=model_name
            )
            
            self.local_llm = LocalLLMService(config)
            self.local_llm.initialize()
            
            logger.info(f"✅ LLM reconfigurado: {model_type}/{model_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao reconfigurar LLM: {e}")
            return False


# Instância global do serviço offline
offline_wikipedia_service = OfflineWikipediaService()