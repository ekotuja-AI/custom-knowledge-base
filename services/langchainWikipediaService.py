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
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ LangChain não disponível: {e}")

    # Fallback dummy classes
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
        def split_documents(self, documents: List['Document']) -> List['Document']:
            chunks = []
            for doc in documents:
                text = doc.page_content
                chunk_size = self.chunk_size
                overlap = self.chunk_overlap
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
    def _criar_colecao(self):
        """Cria a coleção padrão no Qdrant se não existir"""
        if self.qdrant_client is not None:
            self.criar_colecao_custom(self.collection_name, self.embedding_dimension)
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
    
    def criar_colecao_custom(self, collection_name: str, embedding_dimension: Optional[int] = None):
        """Cria coleção Qdrant customizada para multiusuário"""
        if embedding_dimension is None:
            embedding_dimension = self.embedding_dimension
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            if collection_name not in collection_names:
                logger.info(f"📦 Criando coleção '{collection_name}'")
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                # Criar índice de texto no campo page_content para busca textual
                logger.info("📇 Criando índice de texto para busca textual...")
                try:
                    from qdrant_client.models import TextIndexParams, TokenizerType
                    self.qdrant_client.create_payload_index(
                        collection_name=collection_name,
                        field_name="page_content",
                        field_schema=TextIndexParams(
                            type="text",
                            tokenizer=TokenizerType.WORD,
                            min_token_len=2,
                            max_token_len=20,
                            lowercase=True
                        )
                    )
                    logger.info("✅ Índice de texto criado com sucesso")
                except Exception as idx_error:
                    logger.warning(f"⚠️ Erro ao criar índice de texto: {idx_error}")
                logger.info(f"✅ Coleção '{collection_name}' criada")
            else:
                logger.info(f"📦 Coleção '{collection_name}' já existe")
        except Exception as e:
            logger.error(f"❌ Erro ao criar coleção custom: {e}")
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
    
    def ingerir_documentos(self, documentos: List[WikipediaDocument], colecao: str) -> int:
        """Ingere documentos usando pipeline LangChain completo"""
        if not self._initialized:
            raise Exception("Serviço não inicializado")

        if not documentos:
            logger.warning("Nenhum documento fornecido para ingestão")
            return 0

        logger.info(f"📥 ################### ingerir_documentos # {len(documentos)} documentos na coleção '{colecao}' com LangChain")
        logger.info(f"📥 Iniciando ingestão de {len(documentos)} documentos com LangChain")
        start_time = time.time()


        # Detectar dimensão da coleção Qdrant
        try:
            col_info = self.qdrant_client.get_collection(colecao)
            qdrant_dim = col_info.config.params.vectors.size
            logger.info(f"🔎 Dimensão da coleção '{colecao}': {qdrant_dim}")
        except Exception as e:
            logger.warning(f"⚠️ Coleção '{colecao}' não existe, será criada.")
            col_info = None
            qdrant_dim = None

        # Detectar dimensão do embedding
        test_vec = self.embedding_model.encode("teste")
        if hasattr(test_vec, 'tolist'):
            emb_dim = len(test_vec.tolist())
        else:
            emb_dim = len(test_vec)
        logger.info(f"🔎 Dimensão do embedding: {emb_dim}")

        # Se coleção existe e dimensão está errada, remove e recria
        if qdrant_dim is not None and emb_dim != qdrant_dim:
            logger.warning(f"⚠️ Dimensão incompatível: coleção espera {qdrant_dim}, embedding gera {emb_dim}. Removendo e recriando coleção '{colecao}'...")
            self.qdrant_client.delete_collection(collection_name=colecao)
            self.criar_colecao_custom(colecao, emb_dim)
            qdrant_dim = emb_dim

        # Se coleção não existe, cria com dimensão correta
        if qdrant_dim is None:
            logger.info(f"📦 Criando coleção '{colecao}' com dimensão {emb_dim}")
            self.criar_colecao_custom(colecao, emb_dim)
            qdrant_dim = emb_dim

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
                    self._inserir_lote(points_batch, colecao)
                    points_batch = []

            # Processar lote final
            if points_batch:
                self._inserir_lote(points_batch, colecao)

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
    
    def _inserir_lote(self, points: List[PointStruct], colecao: str):
        """Insere lote de pontos no Qdrant"""
        try:
            # Verificar se collection existe, criar se necessário
            try:
                self.qdrant_client.get_collection(colecao)
            except Exception:
                logger.warning(f"⚠️ Collection '{colecao}' não existe, criando...")
                self._criar_colecao()
            
            self.qdrant_client.upsert(
                collection_name=colecao,
                points=points
            )
            logger.debug(f"📦 Lote de {len(points)} pontos inserido")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir lote: {e}")
            raise
    
    def buscar_documentos(self, query: str, limit: int = 10, score_threshold: float = 0.5, colecao: str = None) -> List[SearchResult]:
        """Busca documentos usando LangChain retriever"""
        if not self._initialized:
            logger.error("❌ Serviço não inicializado - chamando inicializar()")
            try:
                self.inicializar()
            except Exception as e:
                logger.error(f"❌ Falha ao inicializar: {e}")
                return []
            
        self.collection_name = colecao if colecao is not None else self.collection_name    
        logger.info("*******************************************************************")
        logger.info(f"🔍 Buscando focumentos na coleção '{self.collection_name}': '{query}' (limit={limit}, threshold={score_threshold})")
        
        if self.embedding_model is None:
            logger.error("❌ Embedding model não inicializado")
            return []
        
        if self.qdrant_client is None:
            logger.error("❌ Qdrant client não inicializado")
            return []
        
        try:
            logger.info(f"🔍 Buscando: '{query}' (limit={limit}, threshold={score_threshold})")
            
            # Verificar se a coleção tem dados
            try:
                col_info = self.qdrant_client.get_collection(self.collection_name)
                logger.info(f"📊 Coleção '{self.collection_name}': {col_info.points_count} pontos")
                if col_info.points_count == 0:
                    logger.error(f"❌ Coleção '{self.collection_name}' está VAZIA!")
                    return []
            except Exception as e:
                logger.error(f"❌ Erro ao acessar coleção: {e}")
                return []
                # Log dos termos buscados
                palavra_norm = normalizar_texto(palavra)
                logger.info(f"🔍 [Busca textual] Termo original: '{palavra}' | Termo normalizado: '{palavra_norm}'")

            # Detectar nomes próprios (palavras com maiúsculas)
            import re
            palavras = query.split()
            nomes_proprios = []
            
            # Lista de stopwords que podem aparecer no início
            stopwords_inicio = ['o', 'a', 'os', 'as', 'que', 'quem', 'qual', 'quais', 'onde', 'quando', 'como']
            
            for i, palavra in enumerate(palavras):
                palavra_limpa = re.sub(r'[^\w]', '', palavra)
                
                # Se for a primeira palavra, só detectar como nome próprio se não for stopword comum
                if i == 0:
                    # Primeira palavra com maiúscula que NÃO é stopword = provavelmente nome próprio
                    if palavra_limpa and palavra_limpa[0].isupper() and len(palavra_limpa) > 2:
                        if palavra.lower() not in stopwords_inicio:
                            nomes_proprios.append(palavra_limpa)
                else:
                    # Palavras subsequentes com maiúscula = nome próprio
                    if palavra_limpa and palavra_limpa[0].isupper() and len(palavra_limpa) > 2:
                        nomes_proprios.append(palavra_limpa)
            
            if nomes_proprios:
                logger.info(f"🏷️  Nomes próprios detectados: {nomes_proprios}")
            
            # Limpar query removendo stopwords e pontuação para melhorar embedding
            stopwords = ['o', 'que', 'é', 'a', 'de', 'da', 'do', 'um', 'uma', 'os', 'as', 'para', 'com', 'por', 'em', 'no', 'na', 'quem', 'foi']
            palavras_limpas = []
            for palavra in query.split():
                palavra_sem_pont = re.sub(r'[^\w]', '', palavra)  # Remove pontuação
                if palavra_sem_pont.lower() not in stopwords and len(palavra_sem_pont) > 0:
                    palavras_limpas.append(palavra_sem_pont)
            
            query_limpa = ' '.join(palavras_limpas)
            
            # Se a query ficou vazia após remover stopwords, usar original
            if not query_limpa.strip():
                query_limpa = query
            
            logger.info(f"🧹 Query limpa para embedding: '{query_limpa}'")
            
            # Gerar embedding da query LIMPA
            query_vector = self.embedding_model.encode(query_limpa).tolist()
            
            # BUSCA 1: Busca semântica normal
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit * 3,  # Buscar 3x mais para ter margem após boosting
                score_threshold=score_threshold
            )
            
            logger.info(f"📡 Busca semântica retornou {len(search_result)} chunks")
            
            # DEBUG: Mostrar alguns resultados da busca semântica
            if len(search_result) == 0:
                logger.warning(f"⚠️ BUSCA SEMÂNTICA RETORNOU 0 RESULTADOS!")
                logger.warning(f"   Query: '{query}'")
                logger.warning(f"   Query limpa: '{query_limpa}'")
                logger.warning(f"   Collection: {self.collection_name}")
                logger.warning(f"   Score threshold: {score_threshold}")
                
                # Tentar buscar SEM threshold para ver se há algum resultado
                try:
                    test_result = self.qdrant_client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        limit=5,
                        score_threshold=0.0
                    )
                    logger.warning(f"   Com threshold=0.0: {len(test_result)} resultados")
                    if test_result:
                        logger.warning(f"   Melhor score: {test_result[0].score:.4f}")
                except:
                    pass
            
            # BUSCA 2: Busca textual adicional
            search_result_keywords = []
            
            # Se houver nomes próprios detectados, buscar por eles
            if nomes_proprios:
                try:
                    from qdrant_client.models import Filter, FieldCondition, MatchText
                    
                    # Buscar documentos que contenham os nomes próprios no conteúdo
                    filter_conditions = []
                    for nome in nomes_proprios:
                        filter_conditions.append(
                            FieldCondition(
                                key="content",
                                match=MatchText(text=nome)
                            )
                        )
                    
                    # Usar AND (must) para nomes próprios
                    filter_obj = Filter(must=filter_conditions)
                    logger.info(f"🔍 Busca híbrida com AND para nomes próprios: {nomes_proprios}")
                    
                    search_result_keywords = self.qdrant_client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        query_filter=filter_obj,
                        limit=limit * 2,
                        score_threshold=0.0  # Aceitar qualquer score se tem o nome
                    )
                    
                    logger.info(f"🔍 Busca por nomes próprios ({nomes_proprios}) retornou {len(search_result_keywords)} chunks")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro na busca por palavras-chave: {e}")
            
            # BUSCA 3: Para queries sem nomes próprios detectados e com 1-2 palavras significativas
            # (ex: "o que é cusco?" -> palavra significativa: "cusco")
            # fazer busca textual case-insensitive
            # MODIFICADO: sempre fazer busca textual para queries curtas, independente de maiúsculas
            if len(palavras_limpas) <= 3:  # Aumentado de 2 para 3 para capturar mais casos
                try:
                    from qdrant_client.models import Filter, FieldCondition, MatchText
                    
                    # Buscar pela query limpa (sem stopwords/pontuação)
                    logger.info(f"🔍 Query com {len(palavras_limpas)} palavras: '{query_limpa}' - fazendo busca textual")
                    
                    for palavra in palavras_limpas:
                        if len(palavra) > 2:  # Ignorar palavras muito curtas
                            try:
                                # Buscar no content e title
                                filter_obj = Filter(
                                    should=[
                                        FieldCondition(key="content", match=MatchText(text=palavra)),
                                        FieldCondition(key="title", match=MatchText(text=palavra))
                                    ]
                                )
                                
                                keywords_result = self.qdrant_client.search(
                                    collection_name=self.collection_name,
                                    query_vector=query_vector,
                                    query_filter=filter_obj,
                                    limit=limit * 2,
                                    score_threshold=0.0
                                )
                                
                                logger.info(f"🔍 Busca textual por '{palavra}' retornou {len(keywords_result)} chunks")
                                
                                # Adicionar aos resultados com boost
                                for hit in keywords_result:
                                    if hit.id not in [r.id for r in search_result_keywords]:
                                        hit.score = hit.score * 2.0  # Boost para match textual
                                        search_result_keywords.append(hit)
                                        
                            except Exception as e:
                                logger.warning(f"⚠️ Erro na busca textual por '{palavra}': {e}")
                                
                except Exception as e:
                    logger.warning(f"⚠️ Erro na busca textual geral: {e}")
            
            # Combinar resultados (sem duplicatas por ID)
            combined_ids = set()
            combined_results = []
            
            for hit in search_result:
                if hit.id not in combined_ids:
                    combined_results.append(hit)
                    combined_ids.add(hit.id)
            
            for hit in search_result_keywords:
                if hit.id not in combined_ids:
                    # Aplicar boost para resultados com nomes próprios
                    hit.score = hit.score * 1.5
                    logger.info(f"✨ Adicionado por nome próprio: '{hit.payload.get('title')}' chunk {hit.payload.get('chunk_index')} (score: {hit.score:.4f})")
                    combined_results.append(hit)
                    combined_ids.add(hit.id)
            
            logger.info(f"🔗 Após combinar: {len(combined_results)} chunks únicos")
            
            # Usar combined_results em vez de search_result
            search_result = combined_results
            
            logger.info(f"📡 Top 15 resultados combinados:")
            for i, hit in enumerate(sorted(search_result, key=lambda x: x.score, reverse=True)[:15], 1):
                logger.info(f"   {i:2d}. {hit.payload.get('title', 'N/A'):30s} score={hit.score:.4f}")
            
            # Extrair termos da query para boosting
            import re
            import unicodedata
            
            def normalizar_texto(texto):
                """Remove acentos e normaliza texto para comparação"""
                texto_nfd = unicodedata.normalize('NFD', texto)
                texto_sem_acento = ''.join(c for c in texto_nfd if unicodedata.category(c) != 'Mn')
                return texto_sem_acento.lower()
            
            stopwords = ['o', 'que', 'é', 'a', 'de', 'da', 'do', 'um', 'uma', 'os', 'as', 'para', 'com', 'por']
            termos_query = [re.sub(r'[^\w\s]', '', t.lower()) for t in query.split() if t.lower() not in stopwords]
            termos_query = [t for t in termos_query if len(t) > 2]
            termos_query_normalizados = [normalizar_texto(t) for t in termos_query]
            
            # Converter para SearchResult e aplicar boosting
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
                
                # Aplicar boosting de 3x para matches exatos no título
                titulo_normalizado = normalizar_texto(result.title)
                conteudo_normalizado = normalizar_texto(result.content[:200])  # Primeiros 200 chars
                
                # Verificar se algum termo normalizado aparece no título ou conteúdo normalizado
                tem_match = False
                if termos_query_normalizados:
                    for termo_norm in termos_query_normalizados:
                        if termo_norm in titulo_normalizado or termo_norm in conteudo_normalizado:
                            tem_match = True
                            break
                
                if tem_match:
                    result.score = result.score * 3.0
                    logger.info(f"🚀 Boosting aplicado: '{result.title}' - score {hit.score:.4f} → {result.score:.4f}")
                
                results.append(result)
            
            # Reordenar por score após boosting
            results = sorted(results, key=lambda x: x.score, reverse=True)
            
            # NÃO remover duplicatas - permitir múltiplos chunks do mesmo artigo
            # Isso é importante para queries técnicas onde a informação pode estar em chunks específicos
            # Aplicar limite diretamente
            results = results[:limit]
            
            # Unificar chunks por artigo, mantendo apenas o melhor score e um trecho resumido
            artigo_dict = {}
            for r in results:
                if r.title not in artigo_dict:
                    artigo_dict[r.title] = r
                else:
                    if r.score > artigo_dict[r.title].score:
                        artigo_dict[r.title] = r
            resultados_unificados = []
            for artigo in artigo_dict.values():
                artigo.content = artigo.content[:200] + ("..." if len(artigo.content) > 200 else "")
                resultados_unificados.append(artigo)
            resultados_unificados = sorted(resultados_unificados, key=lambda x: x.score, reverse=True)[:limit]
            if len(resultados_unificados) == 0:
                logger.warning(f"⚠️⚠️⚠️ RETORNANDO 0 RESULTADOS PARA '{query}' ⚠️⚠️⚠️")
            else:
                logger.info(f"✅ Encontrou {len(resultados_unificados)} artigos (top scores: {[round(r.score, 4) for r in resultados_unificados[:3]]})")
                logger.info(f"📄 Artigos: {list(set([r.title for r in resultados_unificados]))}")
            return resultados_unificados
            
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