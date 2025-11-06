"""
Wikipedia Offline Service - Versão com LangChain

Versão que integra Qdrant + Ollama + dados da Wikipedia com LangChain
"""

import os
import time
import logging
import requests
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# LangChain integration
from .langchainWikipediaService import langchain_wikipedia_service, WikipediaDocument

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


class WikipediaOfflineService:
    """Serviço Wikipedia offline funcional"""
    
    def __init__(self):
        self.client = None
        self.collection_name = "wikipedia_offline"
        self.ollama_host = os.getenv("OLLAMA_HOST", "ollama")
        self.ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
        self.model_name = os.getenv("LLM_MODEL", "qwen2.5:7b")
        self._initialized = False
        
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
    
    def adicionar_artigo_wikipedia(self, titulo: str) -> int:
        """Adiciona artigo da Wikipedia ao banco vetorial usando LangChain"""
        try:
            # Buscar artigo na Wikipedia
            logger.info(f"📖 Buscando artigo: {titulo}")
            artigo = self._buscar_artigo_wikipedia(titulo)
            
            if not artigo:
                logger.warning(f"⚠️ Artigo '{titulo}' não encontrado")
                return 0
            
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
            chunks_criados = langchain_wikipedia_service.ingerir_documentos([documento])
            logger.info(f"✅ {chunks_criados} chunks criados com LangChain para '{titulo}'")
            
            # Também adicionar ao sistema legado para compatibilidade
            chunks_legado = self._processar_e_armazenar_artigo(artigo)
            
            return chunks_criados
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar artigo '{titulo}': {e}")
            return 0
    
    def adicionar_artigos_com_langchain(self, titulos: List[str]) -> Dict[str, int]:
        """Adiciona múltiplos artigos usando pipeline LangChain"""
        try:
            logger.info(f"🔗 Processando {len(titulos)} artigos com LangChain")
            
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
            
            if documentos:
                # Ingestão em lote com LangChain
                total_chunks = langchain_wikipedia_service.ingerir_documentos(documentos)
                chunks_por_doc = total_chunks // len(documentos) if documentos else 0
                
                # Atualizar resultados
                for titulo in resultados:
                    if resultados[titulo] == 0 and any(d.title == titulo for d in documentos):
                        resultados[titulo] = chunks_por_doc
                
                logger.info(f"✅ Ingestão LangChain completa: {total_chunks} chunks para {len(documentos)} documentos")
            
            return resultados
            
        except Exception as e:
            logger.error(f"❌ Erro na ingestão em lote: {e}")
            return {titulo: 0 for titulo in titulos}
    
    def adicionar_chunk_direto(self, chunk_data: Dict) -> bool:
        """Adiciona um chunk já processado diretamente ao banco vetorial"""
        try:
            # Gerar ID único como UUID
            chunk_id = str(uuid.uuid4())
            
            # Preparar payload para Qdrant (sem embedding por enquanto, igual ao método existente)
            payload = {
                "content": chunk_data['content'],
                "title": chunk_data['title'],
                "url": chunk_data['url'],
                "chunk_index": chunk_data.get('chunk_index', 0),
                "total_chunks": chunk_data.get('total_chunks', 1),
                "article_id": str(chunk_data.get('article_id', '')),
                "timestamp": chunk_data.get('timestamp', ''),
                "source": chunk_data.get('source', 'wikipedia_dump')
            }
            
            # Usar um vetor dummy (todos zeros) por enquanto, como no método existente
            dummy_vector = [0.0] * 384  # 384 dimensões
            
            # Criar ponto para Qdrant
            point = PointStruct(
                id=chunk_id,
                vector=dummy_vector,
                payload=payload
            )
            
            # Inserir no Qdrant
            resultado = self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar chunk: {e}")
            return False
    
    def _buscar_artigo_wikipedia(self, titulo: str) -> Optional[Dict]:
        """Busca artigo na Wikipedia API"""
        try:
            # Headers com User-Agent apropriado
            headers = {
                'User-Agent': 'WikipediaOfflineBot/1.0 (https://example.com/contact) Python/3.11'
            }
            
            # URL da API da Wikipedia em português
            url = "https://pt.wikipedia.org/api/rest_v1/page/summary/" + titulo.replace(" ", "_")
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Buscar conteúdo completo
                content_url = f"https://pt.wikipedia.org/api/rest_v1/page/mobile-sections/{titulo.replace(' ', '_')}"
                content_response = requests.get(content_url, headers=headers, timeout=10)
                
                content = ""
                if content_response.status_code == 200:
                    content_data = content_response.json()
                    sections = content_data.get('sections', [])
                    content_parts = []
                    for section in sections:
                        if section.get('text'):
                            content_parts.append(section['text'])
                    content = " ".join(content_parts)
                
                return {
                    'title': data.get('title', titulo),
                    'extract': data.get('extract', ''),
                    'content': content,
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'description': data.get('description', '')
                }
            else:
                logger.warning(f"⚠️ Wikipedia API retornou status {response.status_code} para '{titulo}'")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar artigo na Wikipedia: {e}")
            return None
    
    def _processar_e_armazenar_artigo(self, artigo: Dict) -> int:
        """Processa artigo em chunks e armazena no Qdrant"""
        if not self.client:
            return 0
            
        try:
            # Combinar extract e content
            texto_completo = f"{artigo['extract']} {artigo['content']}"
            
            # Dividir em chunks simples (por parágrafos)
            chunks = self._dividir_em_chunks(texto_completo)
            
            points = []
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Ignorar chunks muito pequenos
                    continue
                    
                # Para simplificar, vamos usar um vetor fake por enquanto
                # Em produção, usaríamos sentence-transformers aqui
                fake_vector = [0.1] * 384  # Vetor de 384 dimensões
                
                # Gerar ID único como UUID
                point_id = str(uuid.uuid4())
                
                point = models.PointStruct(
                    id=point_id,
                    vector=fake_vector,
                    payload={
                        "title": artigo['title'],
                        "content": chunk,
                        "url": artigo['url'],
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "description": artigo.get('description', ''),
                        "source": "wikipedia"
                    }
                )
                points.append(point)
            
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
            return len(points)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar artigo: {e}")
            return 0
    
    def _dividir_em_chunks(self, texto: str, max_size: int = 1000) -> List[str]:
        """Divide texto em chunks por parágrafos"""
        # Dividir por quebras de linha duplas (parágrafos)
        paragrafos = texto.split('\n\n')
        chunks = []
        chunk_atual = ""
        
        for paragrafo in paragrafos:
            paragrafo = paragrafo.strip()
            if not paragrafo:
                continue
                
            if len(chunk_atual) + len(paragrafo) < max_size:
                chunk_atual += paragrafo + "\n\n"
            else:
                if chunk_atual:
                    chunks.append(chunk_atual.strip())
                chunk_atual = paragrafo + "\n\n"
        
        if chunk_atual:
            chunks.append(chunk_atual.strip())
            
        return chunks
    
    def buscar_artigos(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Busca artigos usando LangChain retriever e fallback para sistema legado"""
        try:
            logger.info(f"🔍 Buscando por: '{query}' (limite: {limit})")
            
            # Primeiro: tentar busca com LangChain
            try:
                logger.info("🔗 Tentando busca com LangChain...")
                langchain_results = langchain_wikipedia_service.buscar_documentos(
                    query=query, 
                    limit=limit,
                    score_threshold=0.7
                )
                
                if langchain_results:
                    logger.info(f"✅ LangChain encontrou {len(langchain_results)} resultados")
                    return langchain_results
                else:
                    logger.info("⚠️ LangChain não encontrou resultados, tentando sistema legado...")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro na busca LangChain: {e}, usando sistema legado...")
            
            # Fallback: usar sistema legado
            return self._buscar_artigos_legado(query, limit)
            
        except Exception as e:
            logger.error(f"❌ Erro geral na busca: {e}")
            return self._get_sample_results(query, limit)
    
    def _buscar_artigos_legado(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Sistema de busca legado (backup)"""
        if not self.client:
            return self._get_sample_results(query, limit)
            
        try:
            logger.info(f"🔍 Busca legado por: '{query}' (limite: {limit})")
            
            # Estratégia 1: Tentar busca por texto em múltiplos campos
            search_results = None
            query_terms = query.lower().split()
            
            # Primeiro: tentar MatchText no conteúdo
            try:
                search_results = self.client.scroll(
                    collection_name=self.collection_name,
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
            
            # Se não encontrou resultados, tentar busca no título
            if not search_results or len(search_results[0]) == 0:
                try:
                    search_results = self.client.scroll(
                        collection_name=self.collection_name,
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
            
            # Se ainda não encontrou, fazer busca mais ampla sem filtros e filtrar manualmente
            if not search_results or len(search_results[0]) == 0:
                logger.info("🔄 Tentando busca manual em todos os documentos...")
                try:
                    # Buscar todos os documentos (limitado para não sobrecarregar)
                    all_results = self.client.scroll(
                        collection_name=self.collection_name,
                        limit=500,  # Buscar até 500 documentos
                        with_payload=True
                    )
                    
                    logger.info(f"📚 Encontrou {len(all_results[0])} documentos totais")
                    
                    # Filtrar manualmente por palavras-chave
                    filtered_results = []
                    for hit in all_results[0]:
                        content = hit.payload.get("content", "").lower()
                        title = hit.payload.get("title", "").lower()
                        
                        # Verificar se algum termo da query está no título ou conteúdo
                        score = 0
                        for term in query_terms:
                            if term in title:
                                score += 3  # Título tem peso maior
                            if term in content:
                                score += 1  # Conteúdo tem peso menor
                        
                        if score > 0:
                            filtered_results.append((hit, score))
                    
                    # Ordenar por score e pegar os melhores
                    filtered_results.sort(key=lambda x: x[1], reverse=True)
                    search_results = ([item[0] for item in filtered_results[:limit]], None)
                    
                    logger.info(f"✅ Busca manual encontrou {len(search_results[0])} resultados relevantes")
                    
                except Exception as e:
                    logger.error(f"❌ Erro na busca manual: {e}")
                    search_results = ([], None)
            
            # Processar resultados encontrados
            results = []
            if search_results and len(search_results[0]) > 0:
                for hit in search_results[0]:
                    # Calcular score baseado na relevância dos termos
                    content = hit.payload.get("content", "").lower()
                    title = hit.payload.get("title", "").lower()
                    
                    score = 0.5  # Score base
                    for term in query_terms:
                        if term in title:
                            score += 0.3
                        if term in content:
                            score += 0.1
                    
                    score = min(score, 1.0)  # Limitar a 1.0
                    
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
            
            # Se realmente não encontrou nada, tentar busca de exemplo como último recurso
            logger.warning("⚠️ Nenhum resultado encontrado, usando fallback")
            return self._get_sample_results(query, limit)
                
        except Exception as e:
            logger.error(f"❌ Erro geral na busca: {e}")
            return self._get_sample_results(query, limit)
    
    def perguntar_com_rag(self, pergunta: str, max_chunks: int = 3) -> RAGResponse:
        """Sistema RAG com Ollama"""
        try:
            # Buscar documentos relevantes
            documentos = self.buscar_artigos(pergunta, limit=max_chunks)
            
            if not documentos:
                return RAGResponse(
                    question=pergunta,
                    answer="Desculpe, não encontrei informações relevantes na base de conhecimento.",
                    sources=[],
                    reasoning="Nenhum documento relevante encontrado",
                    model_info={"status": "no_docs", "model": self.model_name}
                )
            
            logger.info(f"📚 Encontrou {len(documentos)} documentos para RAG")
            
            # Preparar contexto otimizado (limitar cada documento a 400 caracteres)
            context_parts = []
            for i, doc in enumerate(documentos, 1):
                # Truncar conteúdo para evitar contexto muito longo
                content_snippet = doc.content[:400]
                if len(doc.content) > 400:
                    content_snippet += "..."
                
                context_parts.append(f"Documento {i} - {doc.title}:\n{content_snippet}")
            
            context = "\n\n".join(context_parts)
            logger.info(f"📝 Contexto preparado com {len(context)} caracteres")
            
            # Gerar resposta com Ollama
            resposta = self._generate_answer_with_ollama(pergunta, context)
            
            return RAGResponse(
                question=pergunta,
                answer=resposta,
                sources=documentos,
                reasoning=f"Resposta gerada com {self.model_name} baseada em {len(documentos)} fontes",
                model_info={"status": "ok", "model": self.model_name}
            )
            
        except Exception as e:
            logger.error(f"❌ Erro no RAG: {e}")
            return RAGResponse(
                question=pergunta,
                answer=f"Erro ao processar pergunta: {str(e)}",
                sources=[],
                reasoning=f"Erro técnico: {str(e)}",
                model_info={"status": "error", "model": "none"}
            )
    
    def _generate_answer_with_ollama(self, question: str, context: str) -> str:
        """Gera resposta usando Ollama"""
        try:
            # Limitar o tamanho do contexto para evitar timeouts
            max_context_length = 3000  # Aproximadamente 3000 caracteres
            if len(context) > max_context_length:
                context = context[:max_context_length] + "...\n[Contexto truncado para melhor performance]"
                logger.info(f"📝 Contexto truncado para {max_context_length} caracteres")
            
            prompt = f"""Você é um assistente especializado em responder perguntas com base em documentos da Wikipedia.

Contexto relevante da Wikipedia:
{context}

Pergunta: {question}

Instruções:
- Use as informações do contexto acima para responder
- Se o contexto contém informações parcialmente relacionadas, use seu conhecimento geral para complementar
- Seja claro, conciso e informativo
- Se não houver informação suficiente, responda com base no que você sabe sobre o tema
- Cite quando possível de onde vem a informação

Resposta:"""

            logger.info(f"🤖 Enviando prompt para Ollama (tamanho: {len(prompt)} caracteres)")
            
            url = f"http://{self.ollama_host}:{self.ollama_port}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,  # Aumentado para respostas mais criativas e completas
                    "top_p": 0.9,        # Aumentado para mais diversidade
                    "max_tokens": 512,   # Aumentado para respostas mais detalhadas
                    "num_ctx": 8192,     # Aumentado - qwen2.5 suporta até 128K
                    "repeat_penalty": 1.1,
                    "top_k": 40
                }
            }
            
            logger.info(f"⏱️ Aguardando resposta do Ollama (timeout: 600s)...")
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=600)  # Aumentado para 10 minutos
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('response', 'Erro ao gerar resposta').strip()
                processing_time = end_time - start_time
                logger.info(f"✅ Resposta gerada em {processing_time:.1f}s (tamanho: {len(answer)} caracteres)")
                return answer
            else:
                logger.error(f"❌ Ollama respondeu com status {response.status_code}")
                return "Erro: LLM não disponível no momento."
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Timeout ao gerar resposta (>600s). Tente uma pergunta mais específica.")
            return "Timeout: A pergunta demorou muito para ser processada. Tente ser mais específico ou use menos contexto."
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta com Ollama: {e}")
            return f"Erro ao gerar resposta: {str(e)}"
    
    def _get_sample_results(self, query: str, limit: int) -> List[SearchResult]:
        """Resultados de exemplo para fallback"""
        logger.warning(f"🔄 Usando resultados de fallback para query: '{query}'")
        
        sample_results = [
            SearchResult(
                title="Base de Conhecimento Vazia",
                content=f"Não foram encontrados resultados para '{query}'. Isto pode indicar que: 1) A base de conhecimento não contém informações sobre este tópico, 2) Os termos de busca não correspondem ao conteúdo disponível, 3) Há um problema técnico na busca. Tente termos mais genéricos ou verifique se o conteúdo foi carregado corretamente na base.",
                url="",
                score=0.1,
                categories=["Sistema", "Fallback"]
            ),
            SearchResult(
                title="Inteligência Artificial",
                content="A inteligência artificial (IA) é um campo da ciência da computação dedicado ao desenvolvimento de sistemas capazes de realizar tarefas que normalmente requerem inteligência humana, como reconhecimento de padrões, tomada de decisões e processamento de linguagem natural.",
                url="https://pt.wikipedia.org/wiki/Inteligência_artificial",
                score=0.05,
                categories=["Tecnologia", "Ciência da Computação", "Exemplo"]
            ),
            SearchResult(
                title="Machine Learning",
                content="Aprendizado de máquina é um subcampo da inteligência artificial que se concentra no desenvolvimento de algoritmos que podem aprender e fazer previsões ou decisões baseadas em dados, sem serem explicitamente programados para cada tarefa específica.",
                url="https://pt.wikipedia.org/wiki/Aprendizado_de_máquina",
                score=0.05,
                categories=["Tecnologia", "Algoritmos", "Exemplo"]
            )
        ]
        
        # Filtrar por relevância básica
        query_lower = query.lower()
        filtered_results = []
        
        # Sempre incluir o resultado de "Base Vazia" primeiro
        filtered_results.append(sample_results[0])
        
        # Adicionar outros resultados se houver alguma relevância
        for result in sample_results[1:]:
            if any(word in result.title.lower() or word in result.content.lower() 
                   for word in query_lower.split()):
                filtered_results.append(result)
        
        # Se não encontrou relevância, adicionar os exemplos mesmo assim
        if len(filtered_results) == 1:  # Só tem o resultado de "Base Vazia"
            filtered_results.extend(sample_results[1:])
        
        return filtered_results[:limit]
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Estatísticas da base Wikipedia"""
        try:
            if self.client:
                collection_info = self.client.get_collection(self.collection_name)
                return {
                    "sistema_offline": True,
                    "colecao": self.collection_name,
                    "total_chunks": collection_info.points_count,
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
                    "status": "modo_exemplo"
                }
        except Exception as e:
            return {"erro": f"Erro ao obter estatísticas: {str(e)}"}
    
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
            self._criar_colecao()
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
    
    def verificar_status(self) -> Dict[str, Any]:
        """Status completo do sistema"""
        # Verifica número de coleções no Qdrant
        colecoes_count = 0
        if self.client:
            try:
                colecoes_count = len(self.client.get_collections().collections)
            except Exception:
                colecoes_count = 0

        # Campos obrigatórios do modelo StatusResponse
        return {
            "status": "ok" if self._initialized else "error",
            "qdrant_conectado": self.client is not None,
            "colecoes": colecoes_count,
            "modelo_embedding_carregado": True,  # ajuste conforme lógica real
            "text_splitter_configurado": True,    # ajuste conforme lógica real
            "openai_configurado": False,          # ajuste conforme lógica real
            "inicializado": self._initialized
        }
    
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