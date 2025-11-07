"""
LangChain Wikipedia Service - Implementação correta do LangChain

Este serviço implementa corretamente o pipeline LangChain para:
- Ingestão de documentos da Wikipedia
- Processamento com TextSplitters
- Criação de embeddings
- Armazenamento no Qdrant

Graceful fallback se LangChain não estiver disponível.
"""

import os
import time
import logging
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Try to import LangChain - fallback gracefully if not available
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from langchain.schema import BaseRetriever
    from langchain.callbacks.manager import CallbackManagerForRetrieverRun
    LANGCHAIN_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ LangChain disponível")
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ LangChain não disponível: {e}")
    
    # Create dummy classes for compatibility
    class Document:
        def __init__(self, page_content: str, metadata: Dict[str, Any]):
            self.page_content = page_content
            self.metadata = metadata
    
    class BaseRetriever:
        pass
    
    class CallbackManagerForRetrieverRun:
        pass
    
    class RecursiveCharacterTextSplitter:
        def __init__(self, **kwargs):
            self.chunk_size = kwargs.get('chunk_size', 1000)
            self.chunk_overlap = kwargs.get('chunk_overlap', 200)
        
        def split_documents(self, documents: List[Document]) -> List[Document]:
            """Fallback text splitter"""
            chunks = []
            for doc in documents:
                text = doc.page_content
                chunk_size = self.chunk_size
                overlap = self.chunk_overlap
                
                # Simple text splitting
                start = 0
                while start < len(text):
                    end = start + chunk_size
                    chunk_text = text[start:end]
                    
                    chunk = Document(
                        page_content=chunk_text,
                        metadata=doc.metadata.copy()
                    )
                    chunks.append(chunk)
                    
                    start = end - overlap
                    if start >= len(text):
                        break
                        
            return chunks

# Vector store and embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️ SentenceTransformers não disponível")
    
    # Dummy class for compatibility
    class SentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name
            logger.warning(f"⚠️ SentenceTransformer simulado: {model_name}")
        
        def encode(self, text):
            # Return dummy vector
            return [0.1] * 384

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("⚠️ Qdrant não disponível")
    
    # Dummy classes
    class QdrantClient:
        def __init__(self, **kwargs):
            pass
    
    class Distance:
        COSINE = "cosine"
    
    class VectorParams:
        def __init__(self, **kwargs):
            pass
    
    class PointStruct:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)


@dataclass
class WikipediaDocument:
    """Documento da Wikipedia processado"""
    title: str
    content: str
    url: str
    metadata: Dict[str, Any]


@dataclass 
class SearchResult:
    """Resultado de busca com LangChain"""
    title: str
    content: str
    url: str
    score: float
    metadata: Dict[str, Any]


class QdrantRetriever(BaseRetriever):
    """Retriever personalizado para Qdrant com LangChain"""
    
    qdrant_client: Any
    collection_name: str
    embedding_model: Any
    
    def __init__(self, qdrant_client: QdrantClient, collection_name: str, embedding_model: SentenceTransformer):
        super().__init__(
            qdrant_client=qdrant_client,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun, **kwargs
    ) -> List[Document]:
        """Busca documentos relevantes no Qdrant"""
        try:
            # Gerar embedding da query
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Buscar no Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=kwargs.get('limit', 10),
                score_threshold=kwargs.get('score_threshold', 0.7)
            )
            
            # Converter para documentos LangChain
            documents = []
            for hit in search_result:
                doc = Document(
                    page_content=hit.payload.get('content', ''),
                    metadata={
                        'title': hit.payload.get('title', ''),
                        'url': hit.payload.get('url', ''),
                        'score': hit.score,
                        'chunk_index': hit.payload.get('chunk_index', 0),
                        'total_chunks': hit.payload.get('total_chunks', 1)
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {e}")
            return []


class LangChainWikipediaService:
    """Serviço Wikipedia com LangChain completo (com fallback)"""
    
    def __init__(self):
        self.qdrant_client = None
        self.embedding_model = None
        self.text_splitter = None
        self.retriever = None
        self.collection_name = "wikipedia_langchain"
        self._initialized = False
        
        # Configurações
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.embedding_dimension = 384
        
        # Status de disponibilidade
        self.langchain_available = LANGCHAIN_AVAILABLE
        self.sentence_transformers_available = SENTENCE_TRANSFORMERS_AVAILABLE
        self.qdrant_available = QDRANT_AVAILABLE
        
    def inicializar(self):
        """Inicializa o serviço LangChain (com fallbacks)"""
        # Sempre permitir re-inicialização do modelo de embedding
        force_reload_embedding = not self.sentence_transformers_available or self.embedding_model is None
        
        if self._initialized and not force_reload_embedding:
            return
            
        logger.info("🚀 Inicializando LangChain Wikipedia Service...")
        logger.info(f"   📦 LangChain: {'✅' if self.langchain_available else '❌'}")
        logger.info(f"   🤖 SentenceTransformers: {'✅' if self.sentence_transformers_available else '❌'}")
        logger.info(f"   🗄️ Qdrant: {'✅' if self.qdrant_available else '❌'}")
        
        try:
            if self.qdrant_available and not self._initialized:
                self._conectar_qdrant()
                self._criar_colecao()
            
            # Sempre tentar carregar embedding model se ainda não estiver carregado
            if self.embedding_model is None:
                self._carregar_embedding_model()
            
            if not self._initialized:
                self._configurar_text_splitter()
            
            if self.qdrant_available and self.embedding_model is not None and not self._initialized:
                self._configurar_retriever()
            
            self._initialized = True
            status = "completo" if all([self.langchain_available, self.sentence_transformers_available, self.qdrant_available, self.embedding_model is not None]) else "parcial"
            logger.info(f"✅ LangChain Wikipedia Service inicializado ({status})!")
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            # Ainda marca como inicializado em modo degradado
            self._initialized = True
            logger.warning("⚠️ Funcionando em modo degradado")
    
    def _conectar_qdrant(self):
        """Conecta ao Qdrant"""
        if not self.qdrant_available:
            logger.warning("⚠️ Qdrant não disponível - pulando conexão")
            return
            
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", 6333))
        
        logger.info(f"🔗 Conectando ao Qdrant em {host}:{port}")
        self.qdrant_client = QdrantClient(host=host, port=port)
        
        # Testar conexão
        try:
            collections = self.qdrant_client.get_collections()
            logger.info(f"✅ Conectado ao Qdrant - {len(collections.collections)} coleções")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao conectar Qdrant: {e}")
            self.qdrant_client = None
    
    def _carregar_embedding_model(self):
        """Carrega modelo de embeddings"""
        if not self.sentence_transformers_available:
            logger.warning("⚠️ SentenceTransformers não disponível")
            return
            
        model_name = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        logger.info(f"📚 Carregando modelo de embeddings: {model_name}")
        
        try:
            self.embedding_model = SentenceTransformer(model_name)
            logger.info("✅ Modelo de embeddings carregado")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            self.embedding_model = None
    
    def _configurar_text_splitter(self):
        """Configura o TextSplitter"""
        logger.info(f"📄 Configurando TextSplitter - chunk_size: {self.chunk_size}, overlap: {self.chunk_overlap}")
        
        if self.langchain_available:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            logger.info("✅ TextSplitter LangChain configurado")
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            logger.info("✅ TextSplitter fallback configurado")
    
    def _criar_colecao(self):
        """Cria coleção no Qdrant se não existir"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"📦 Criando coleção '{self.collection_name}'")
                
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Coleção '{self.collection_name}' criada")
            else:
                logger.info(f"📦 Coleção '{self.collection_name}' já existe")
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar coleção: {e}")
            raise
    
    def _configurar_retriever(self):
        """Configura o retriever LangChain"""
        logger.info("🔍 Configurando retriever LangChain")
        
        self.retriever = QdrantRetriever(
            qdrant_client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding_model=self.embedding_model
        )
        
        logger.info("✅ Retriever configurado")
    
    def ingerir_documentos(self, documentos: List[WikipediaDocument]) -> int:
        """Ingere documentos usando pipeline LangChain completo"""
        if not self._initialized:
            raise Exception("Serviço não inicializado")
        
        if not documentos:
            logger.warning("Nenhum documento fornecido para ingestão")
            return 0
        
        logger.info(f"📥 Iniciando ingestão de {len(documentos)} documentos com LangChain")
        start_time = time.time()
        
        try:
            total_chunks = 0
            points_batch = []
            
            for doc in documentos:
                # Criar documento LangChain
                langchain_doc = Document(
                    page_content=doc.content,
                    metadata={
                        'title': doc.title,
                        'url': doc.url,
                        **doc.metadata
                    }
                )
                
                # Dividir em chunks com LangChain TextSplitter
                chunks = self.text_splitter.split_documents([langchain_doc])
                
                logger.info(f"📄 '{doc.title}': {len(chunks)} chunks criados")
                
                # Processar cada chunk
                for i, chunk in enumerate(chunks):
                    # Gerar embedding
                    if self.embedding_model is None:
                        logger.error("❌ Modelo de embeddings não disponível")
                        raise RuntimeError("Embedding model não inicializado. Instale sentence-transformers.")
                    
                    embedding_result = self.embedding_model.encode(chunk.page_content)
                    
                    # Converter para lista se necessário
                    if hasattr(embedding_result, 'tolist'):
                        embedding = embedding_result.tolist()
                    else:
                        embedding = list(embedding_result)
                    
                    # Criar ponto para Qdrant
                    point_id = str(uuid.uuid4())
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            'title': chunk.metadata['title'],
                            'content': chunk.page_content,
                            'url': chunk.metadata['url'],
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'doc_metadata': chunk.metadata,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                    )
                    
                    points_batch.append(point)
                    total_chunks += 1
                
                # Processar em lotes de 100
                if len(points_batch) >= 100:
                    self._inserir_lote(points_batch)
                    points_batch = []
            
            # Processar lote final
            if points_batch:
                self._inserir_lote(points_batch)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            logger.info(f"✅ Ingestão concluída:")
            logger.info(f"   📄 Documentos: {len(documentos)}")
            logger.info(f"   🔢 Chunks: {total_chunks}")
            logger.info(f"   ⏱️ Tempo: {processing_time:.2f}s")
            logger.info(f"   🚀 Velocidade: {total_chunks/processing_time:.2f} chunks/s")
            
            return total_chunks
            
        except Exception as e:
            logger.error(f"❌ Erro na ingestão: {e}")
            raise
    
    def _inserir_lote(self, points: List[PointStruct]):
        """Insere lote de pontos no Qdrant"""
        try:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.debug(f"📦 Lote de {len(points)} pontos inserido")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir lote: {e}")
            raise
    
    def buscar_documentos(self, query: str, limit: int = 10, score_threshold: float = 0.5) -> List[SearchResult]:
        """Busca documentos usando LangChain retriever"""
        if not self._initialized:
            raise Exception("Serviço não inicializado")
        
        if self.embedding_model is None:
            logger.error("❌ Embedding model não inicializado")
            return []
        
        try:
            logger.info(f"🔍 Buscando: '{query}' (limit={limit}, threshold={score_threshold})")
            
            # Gerar embedding da query diretamente
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Buscar no Qdrant diretamente
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Converter para SearchResult
            results = []
            for hit in search_result:
                result = SearchResult(
                    title=hit.payload.get('title', ''),
                    content=hit.payload.get('content', ''),
                    url=hit.payload.get('url', ''),
                    score=hit.score,
                    metadata={
                        'chunk_index': hit.payload.get('chunk_index', 0),
                        'total_chunks': hit.payload.get('total_chunks', 1)
                    }
                )
                results.append(result)
            
            logger.info(f"✅ Encontrou {len(results)} documentos")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return []
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas da coleção"""
        if not self._initialized:
            raise Exception("Serviço não inicializado")
        
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "total_points": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.value,
                "status": collection_info.status.value,
                "optimizer_status": collection_info.optimizer_status.value if collection_info.optimizer_status else "unknown"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {"error": str(e)}


# Instância global do serviço
langchain_wikipedia_service = LangChainWikipediaService()