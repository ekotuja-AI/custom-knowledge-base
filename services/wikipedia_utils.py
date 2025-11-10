"""
Utilitários para Wikipedia Offline Service

Classes auxiliares para processamento de texto, API Wikipedia e Qdrant
"""

import logging
import requests
import time
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class WikipediaAPIClient:
    """Cliente para Wikipedia API com múltiplos métodos de busca"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'WikipediaOfflineRAG/2.0 (Educational project; Python/requests) Contact: github.com/ekotuja-AI',
            'Accept': 'application/json'
        }
        self.timeout = 10
    
    def buscar_artigo_completo(self, titulo: str) -> Optional[Dict]:
        """Busca artigo na Wikipedia API com conteúdo completo usando Parse API"""
        try:
            titulo_encoded = titulo.replace(" ", "_")
            
            # 1. Buscar summary para metadados
            summary_url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{titulo_encoded}"
            summary_response = requests.get(summary_url, headers=self.headers, timeout=self.timeout)
            
            if summary_response.status_code != 200:
                logger.warning(f"⚠️ Summary API retornou status {summary_response.status_code} para '{titulo}'")
                return None
            
            summary_data = summary_response.json()
            
            # 2. Buscar conteúdo completo usando Parse API
            parse_url = f"https://pt.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&titles={titulo_encoded}&explaintext=1&exsectionformat=plain"
            parse_response = requests.get(parse_url, headers=self.headers, timeout=self.timeout)
            
            content = ""
            if parse_response.status_code == 200:
                parse_data = parse_response.json()
                pages = parse_data.get('query', {}).get('pages', {})
                
                # Pegar o primeiro (e único) resultado
                for page_id, page_data in pages.items():
                    if page_id != '-1':  # -1 indica página não encontrada
                        content = page_data.get('extract', '')
                        logger.info(f"✅ Conteúdo completo obtido: {len(content)} caracteres")
                    else:
                        logger.warning(f"⚠️ Página não encontrada na Parse API")
            
            # Fallback: se Parse API falhar, usar extract do summary
            if not content.strip():
                content = summary_data.get('extract', '')
                logger.warning(f"⚠️ Usando apenas extract do summary para '{titulo}' ({len(content)} caracteres)")
            
            return {
                'title': summary_data.get('title', titulo),
                'extract': summary_data.get('extract', ''),
                'content': content,
                'url': summary_data.get('content_urls', {}).get('desktop', {}).get('page', f'https://pt.wikipedia.org/wiki/{titulo_encoded}'),
                'description': summary_data.get('description', '')
            }
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar artigo na Wikipedia: {e}", exc_info=True)
            return None


class TextProcessor:
    """Processador de texto para chunking e limpeza"""
    
    @staticmethod
    def criar_chunks(texto: str, tamanho_chunk: int = 500, overlap: int = 50) -> List[str]:
        """Divide texto em chunks com overlap"""
        if not texto:
            return []
        
        palavras = texto.split()
        chunks = []
        i = 0
        
        while i < len(palavras):
            chunk = ' '.join(palavras[i:i + tamanho_chunk])
            chunks.append(chunk)
            i += tamanho_chunk - overlap
        
        return chunks
    
    @staticmethod
    def limpar_query(query: str) -> str:
        """Remove stopwords e normaliza query"""
        stopwords = {'o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'é', 'que', 'qual', 'quais', 'quem', 'foi', 'são'}
        palavras = query.lower().split()
        palavras_limpas = [p for p in palavras if p not in stopwords and len(p) > 2]
        return ' '.join(palavras_limpas)
    
    @staticmethod
    def extrair_termos_query(query: str) -> List[str]:
        """Extrai termos significativos da query"""
        query_limpa = TextProcessor.limpar_query(query)
        return [termo.strip() for termo in query_limpa.split() if len(termo.strip()) > 2]


class QdrantHelper:
    """Auxiliar para operações comuns do Qdrant"""
    
    @staticmethod
    def criar_payload_chunk(chunk_data: Dict) -> Dict:
        """Cria payload padronizado para um chunk"""
        return {
            "content": chunk_data['content'],
            "title": chunk_data['title'],
            "url": chunk_data['url'],
            "chunk_index": chunk_data.get('chunk_index', 0),
            "total_chunks": chunk_data.get('total_chunks', 1),
            "article_id": str(chunk_data.get('article_id', '')),
            "timestamp": chunk_data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S')),
            "source": chunk_data.get('source', 'wikipedia_api')
        }
    
    @staticmethod
    def gerar_id_unico() -> str:
        """Gera ID único para ponto no Qdrant"""
        return str(uuid.uuid4())
    
    @staticmethod
    def criar_vetor_dummy(dimensoes: int = 384) -> List[float]:
        """Cria vetor dummy para compatibilidade"""
        return [0.0] * dimensoes
    
    @staticmethod
    def filtrar_por_score(resultados: List[Any], score_minimo: float) -> List[Any]:
        """Filtra resultados por score mínimo"""
        return [r for r in resultados if hasattr(r, 'score') and r.score >= score_minimo]
    
    @staticmethod
    def calcular_score_relevancia(content: str, title: str, query_terms: List[str]) -> float:
        """Calcula score de relevância baseado em termos da query"""
        content_lower = content.lower()
        title_lower = title.lower()
        
        score = 0.5  # Score base
        for term in query_terms:
            if term in title_lower:
                score += 0.3  # Título tem peso maior
            if term in content_lower:
                score += 0.1  # Conteúdo tem peso menor
        
        return min(score, 1.0)  # Limitar a 1.0


class WikipediaDataValidator:
    """Validador de dados da Wikipedia"""
    
    @staticmethod
    def validar_artigo(artigo: Dict) -> bool:
        """Valida se artigo tem dados mínimos necessários"""
        campos_obrigatorios = ['title', 'content', 'url']
        
        for campo in campos_obrigatorios:
            if campo not in artigo or not artigo[campo]:
                logger.warning(f"⚠️ Artigo inválido: campo '{campo}' ausente ou vazio")
                return False
        
        # Validar tamanho mínimo do conteúdo
        if len(artigo['content']) < 100:
            logger.warning(f"⚠️ Artigo '{artigo['title']}' com conteúdo muito curto ({len(artigo['content'])} chars)")
            return False
        
        return True
    
    @staticmethod
    def validar_chunk(chunk: Dict) -> bool:
        """Valida se chunk tem estrutura correta"""
        campos_obrigatorios = ['content', 'title', 'url']
        
        for campo in campos_obrigatorios:
            if campo not in chunk or not chunk[campo]:
                return False
        
        return True


class MetricsCollector:
    """Coletor de métricas de operação"""
    
    def __init__(self):
        self.metrics = {
            'total_searches': 0,
            'successful_searches': 0,
            'total_articles_processed': 0,
            'total_chunks_created': 0,
            'total_rag_queries': 0,
            'avg_response_time': 0.0
        }
        self.response_times = []
    
    def record_search(self, success: bool):
        """Registra uma busca"""
        self.metrics['total_searches'] += 1
        if success:
            self.metrics['successful_searches'] += 1
    
    def record_article_processed(self, chunks_created: int):
        """Registra processamento de artigo"""
        self.metrics['total_articles_processed'] += 1
        self.metrics['total_chunks_created'] += chunks_created
    
    def record_rag_query(self, response_time: float):
        """Registra query RAG"""
        self.metrics['total_rag_queries'] += 1
        self.response_times.append(response_time)
        
        if self.response_times:
            self.metrics['avg_response_time'] = sum(self.response_times) / len(self.response_times)
    
    def get_metrics(self) -> Dict:
        """Retorna métricas coletadas"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reseta todas as métricas"""
        self.metrics = {
            'total_searches': 0,
            'successful_searches': 0,
            'total_articles_processed': 0,
            'total_chunks_created': 0,
            'total_rag_queries': 0,
            'avg_response_time': 0.0
        }
        self.response_times = []
