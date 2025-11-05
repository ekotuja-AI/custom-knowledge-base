"""
Wikipedia Dump Processor - Processamento de Dumps XML da Wikipedia

Este serviço processa dumps XML da Wikipedia para ingestão em massa.
Suporta diferentes tipos de dumps e processamento em lotes.
"""

import os
import xml.etree.ElementTree as ET
import bz2
import gzip
import requests
import logging
from typing import Dict, List, Generator, Optional, Any
from dataclasses import dataclass
import time
import re
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class WikipediaArticle:
    """Representa um artigo da Wikipedia"""
    title: str
    content: str
    id: int
    timestamp: str
    redirect: Optional[str] = None

@dataclass
class DumpInfo:
    """Informações sobre um dump da Wikipedia"""
    language: str
    date: str
    type: str  # 'pages-articles', 'pages-meta-current', etc.
    url: str
    size_mb: int
    filename: str

class WikipediaDumpProcessor:
    """Processador de dumps XML da Wikipedia"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # URLs base para downloads
        self.base_urls = {
            'pt': 'https://dumps.wikimedia.org/ptwiki/',
            'en': 'https://dumps.wikimedia.org/enwiki/',
            'es': 'https://dumps.wikimedia.org/eswiki/'
        }
        
        # Configurações de processamento
        self.batch_size = 1000  # Artigos por lote
        self.min_content_length = 50  # Tamanho mínimo do conteúdo (reduzido para teste)
        
    def get_available_dumps(self, language: str = 'pt') -> List[DumpInfo]:
        """Lista dumps disponíveis para download"""
        try:
            base_url = self.base_urls.get(language)
            if not base_url:
                raise ValueError(f"Idioma '{language}' não suportado")
            
            # URLs reais dos dumps mais recentes (verificar disponibilidade)
            # Dumps da Wikipedia são criados mensalmente, geralmente no dia 1
            latest_date = "20241001"  # Data mais provável (outubro 2024)
            
            dumps = []
            
            if language == 'pt':
                # Dumps reais da Wikipedia PT - URLs mais prováveis
                dumps = [
                    DumpInfo(
                        language="pt",
                        date=latest_date,
                        type="pages-articles",
                        url=f"https://dumps.wikimedia.org/ptwiki/{latest_date}/ptwiki-{latest_date}-pages-articles.xml.bz2",
                        size_mb=650,  # Tamanho real típico da Wikipedia PT
                        filename=f"ptwiki-{latest_date}-pages-articles.xml.bz2"
                    ),
                    DumpInfo(
                        language="pt", 
                        date=latest_date,
                        type="abstract",
                        url=f"https://dumps.wikimedia.org/ptwiki/{latest_date}/ptwiki-{latest_date}-abstract.xml.gz",
                        size_mb=15,
                        filename=f"ptwiki-{latest_date}-abstract.xml.gz"
                    ),
                    DumpInfo(
                        language="pt",
                        date=latest_date, 
                        type="pages-meta-current",
                        url=f"https://dumps.wikimedia.org/ptwiki/{latest_date}/ptwiki-{latest_date}-pages-meta-current.xml.bz2",
                        size_mb=900,
                        filename=f"ptwiki-{latest_date}-pages-meta-current.xml.bz2"
                    ),
                    # Adicionar dump alternativo com data mais antiga
                    DumpInfo(
                        language="pt",
                        date="20240901",
                        type="pages-articles",
                        url=f"https://dumps.wikimedia.org/ptwiki/20240901/ptwiki-20240901-pages-articles.xml.bz2",
                        size_mb=650,
                        filename=f"ptwiki-20240901-pages-articles.xml.bz2"
                    )
                ]
            
            return dumps
            
        except Exception as e:
            logger.error(f"Erro ao listar dumps: {e}")
            return []
    
    def download_dump(self, dump_info: DumpInfo, progress_callback=None) -> str:
        """Download de um dump com barra de progresso"""
        try:
            filepath = self.data_dir / dump_info.filename
            
            # Verificar se já existe
            if filepath.exists():
                logger.info(f"✅ Dump já existe: {filepath}")
                return str(filepath)
            
            logger.info(f"📥 Iniciando download: {dump_info.filename}")
            logger.info(f"🔗 URL: {dump_info.url}")
            logger.info(f"📊 Tamanho estimado: {dump_info.size_mb} MB")
            
            response = requests.get(dump_info.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress, downloaded, total_size)
            
            logger.info(f"✅ Download concluído: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Erro no download: {e}")
            raise
    
    def parse_xml_dump(self, filepath: str) -> Generator[WikipediaArticle, None, None]:
        """Parser XML eficiente para dumps da Wikipedia"""
        try:
            logger.info(f"📖 Iniciando parsing: {filepath}")
            
            # Verificar se arquivo existe
            if not os.path.exists(filepath):
                logger.error(f"❌ Arquivo não encontrado: {filepath}")
                return
            
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logger.info(f"📁 Tamanho do arquivo: {file_size_mb:.1f} MB")
            
            # Detectar tipo de compressão
            if filepath.endswith('.bz2'):
                logger.info("🗜️ Descomprimindo arquivo BZ2...")
                file_obj = bz2.open(filepath, 'rt', encoding='utf-8')
            elif filepath.endswith('.gz'):
                logger.info("🗜️ Descomprimindo arquivo GZ...")
                file_obj = gzip.open(filepath, 'rt', encoding='utf-8')
            else:
                logger.info("📄 Lendo arquivo XML direto...")
                file_obj = open(filepath, 'r', encoding='utf-8')
            
            # Namespaces XML da Wikipedia (suporte a várias versões)
            namespaces = {
                'mw': 'http://www.mediawiki.org/xml/export-0.11/',
                'mw10': 'http://www.mediawiki.org/xml/export-0.10/'
            }
            
            articles_count = 0
            page_count = 0
            
            with file_obj as f:
                logger.info("🔍 Iniciando parsing XML...")
                
                # Tentar ler algumas linhas primeiro para debug
                try:
                    first_line = f.readline()
                    logger.info(f"📝 Primeira linha: {first_line[:100]}...")
                    f.seek(0)  # Voltar ao início
                except Exception as e:
                    logger.error(f"❌ Erro ao ler primeira linha: {e}")
                    return
                
                # Parser iterativo para economizar memória
                try:
                    logger.info("🔍 Iniciando iterparse com namespaces...")
                    # Usar eventos mais simples para debug
                    for event, elem in ET.iterparse(f, events=('start', 'end')):
                        if event == 'end':
                            # Verificar se é elemento page (mais flexível)
                            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                            
                            if tag_name == 'page':
                                page_count += 1
                                logger.info(f"🔍 Página {page_count} encontrada: tag completa={elem.tag}")
                                
                                try:
                                    article = self._extract_article_from_element(elem, namespaces)
                                    if article:
                                        logger.info(f"📄 Artigo extraído: {article.title} (válido: {self._is_valid_article(article)})")
                                        if self._is_valid_article(article):
                                            yield article
                                            articles_count += 1
                                            
                                            if articles_count == 1:
                                                logger.info(f"✅ Primeiro artigo válido: {article.title}")
                                            elif articles_count % 10 == 0:
                                                logger.info(f"📚 Processados {articles_count} artigos válidos...")
                                    else:
                                        logger.info(f"❌ Falha ao extrair artigo da página {page_count}")
                                
                                except Exception as e:
                                    logger.warning(f"⚠️ Erro ao processar página {page_count}: {e}")
                                
                                finally:
                                    # Limpar elemento para economizar memória
                                    elem.clear()
                                    
                except Exception as e:
                    logger.error(f"❌ Erro ao inicializar parser XML: {e}")
                    return
            
            logger.info(f"📊 Estatísticas finais: {page_count} páginas encontradas, {articles_count} artigos válidos")
            logger.info(f"✅ Parsing concluído: {articles_count} artigos válidos processados")
            
        except Exception as e:
            logger.error(f"❌ Erro no parsing XML: {e}")
            import traceback
            logger.error(f"📋 Stack trace: {traceback.format_exc()}")
            raise
    
    def _extract_article_from_element(self, page_elem, namespaces: Dict) -> Optional[WikipediaArticle]:
        """Extrai dados de um elemento page XML"""
        try:
            # Extrair título
            # Tentar extrair com namespace
            title_elem = page_elem.find('.//mw:title', namespaces)
            if title_elem is None:
                title_elem = page_elem.find('.//title')
            if title_elem is None:
                logger.info("❌ Título não encontrado na página.")
                return None
            title = title_elem.text

            # Extrair ID
            id_elem = page_elem.find('.//mw:id', namespaces)
            if id_elem is None:
                id_elem = page_elem.find('.//id')
            page_id = int(id_elem.text) if id_elem is not None else 0

            # Extrair conteúdo da revisão mais recente
            revision = page_elem.find('.//mw:revision', namespaces)
            if revision is None:
                revision = page_elem.find('.//revision')
            if revision is None:
                logger.info(f"❌ Revisão não encontrada para artigo '{title}'.")
                return None

            text_elem = revision.find('.//mw:text', namespaces)
            if text_elem is None:
                text_elem = revision.find('.//text')
            if text_elem is None:
                logger.info(f"❌ Tag <text> não encontrada para artigo '{title}'.")
                return None

            content = text_elem.text or ""
            logger.info(f"📝 Artigo extraído: '{title}' | Tamanho do conteúdo: {len(content)} chars")

            # Extrair timestamp
            timestamp_elem = revision.find('.//mw:timestamp', namespaces)
            if timestamp_elem is None:
                timestamp_elem = revision.find('.//timestamp')
            timestamp = timestamp_elem.text if timestamp_elem is not None else ""

            # Verificar se é redirecionamento
            redirect = None
            if content.strip().startswith('#REDIRECT'):
                redirect_match = re.search(r'#REDIRECT\s*\[\[([^\]]+)\]\]', content, re.IGNORECASE)
                if redirect_match:
                    redirect = redirect_match.group(1)
                logger.info(f"⏭️ Artigo '{title}' é redirecionamento para '{redirect}'.")

            article_obj = WikipediaArticle(
                title=title,
                content=content,
                id=page_id,
                timestamp=timestamp,
                redirect=redirect
            )

            # Motivo do descarte (se ocorrer)
            if redirect:
                logger.info(f"⏭️ Artigo '{title}' descartado: redirecionamento.")
            elif len(content) < self.min_content_length:
                logger.info(f"⏭️ Artigo '{title}' descartado: conteúdo muito pequeno ({len(content)} chars).")
            elif '{{desambiguação}}' in content.lower() or '{{disambig}}' in content.lower():
                logger.info(f"⏭️ Artigo '{title}' descartado: desambiguação.")

            return article_obj

        except Exception as e:
            logger.warning(f"⚠️ Erro ao extrair artigo: {e}")
            return None
    
    def _is_valid_article(self, article: WikipediaArticle) -> bool:
        """Verifica se um artigo é válido para processamento"""
        # Filtrar por namespace (apenas artigos principais)
        if ':' in article.title and not article.title.startswith('Categoria:'):
            # Excluir páginas de discussão, usuário, etc.
            excluded_prefixes = [
                'Discussão:', 'Usuário:', 'Wikipedia:', 'Ficheiro:', 
                'MediaWiki:', 'Predefinição:', 'Ajuda:', 'Portal:',
                'Anexo:', 'Livro:', 'Módulo:', 'Especial:'
            ]
            
            for prefix in excluded_prefixes:
                if article.title.startswith(prefix):
                    return False
        
        # Excluir redirecionamentos
        if article.redirect:
            return False
        
        # Filtrar por tamanho mínimo
        if len(article.content) < self.min_content_length:
            return False
        
        # Excluir páginas de desambiguação
        if '{{desambiguação}}' in article.content.lower() or '{{disambig}}' in article.content.lower():
            return False
        
        return True
    
    def clean_wikitext(self, wikitext: str) -> str:
        """Remove marcação wiki e retorna texto limpo"""
        # Remove templates {{...}}
        text = re.sub(r'\{\{[^}]*\}\}', '', wikitext)
        
        # Remove links [[...]]
        text = re.sub(r'\[\[([^|\]]*\|)?([^\]]*)\]\]', r'\2', text)
        
        # Remove referências <ref>...</ref>
        text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
        text = re.sub(r'<ref[^>]*/?>', '', text)
        
        # Remove outros elementos HTML
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove categorias
        text = re.sub(r'\[\[Categoria:.*?\]\]', '', text)
        
        # Remove múltiplas quebras de linha
        text = re.sub(r'\n+', '\n', text)
        
        # Remove espaços extras
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def process_dump_to_chunks(self, filepath: str, max_articles: int = None) -> Generator[Dict, None, None]:
        """Processa dump e gera chunks prontos para ingestão"""
        processed = 0
        logger.info(f"🚀 Iniciando process_dump_to_chunks: {filepath}")
        logger.info(f"📊 Limite máximo de artigos: {max_articles}")
        try:
            article_count = 0
            offset = getattr(self, 'offset', 0)
            for article in self.parse_xml_dump(filepath):
                article_count += 1
                if offset and article_count <= offset:
                    continue
                logger.info(f"📖 Artigo {article_count}: {article.title}")
                if max_articles and processed >= max_articles:
                    logger.info(f"🛑 Limite de {max_articles} artigos atingido")
                    break
                try:
                    # Limpar conteúdo
                    clean_content = self.clean_wikitext(article.content)
                    if len(clean_content) < self.min_content_length:
                        logger.info(f"⏭️ Artigo descartado: '{article.title}' ({len(clean_content)} chars)")
                        continue
                    # Dividir em chunks
                    chunks = self._split_into_chunks(clean_content)
                    logger.info(f"🧩 Artigo '{article.title}' gerou {len(chunks)} chunks")
                    for i, chunk in enumerate(chunks):
                        yield {
                            'title': article.title,
                            'content': chunk,
                            'url': f"https://pt.wikipedia.org/wiki/{article.title.replace(' ', '_')}",
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'article_id': article.id,
                            'timestamp': article.timestamp,
                            'source': 'wikipedia_dump'
                        }
                    
                    processed += 1
                    
                    if processed % 100 == 0:
                        logger.info(f"🔄 Processados {processed} artigos em chunks")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar artigo '{article.title}': {e}")
                    continue
                    
            logger.info(f"🏁 process_dump_to_chunks concluído: {processed} artigos processados de {article_count} encontrados")
            
        except Exception as e:
            logger.error(f"❌ Erro crítico em process_dump_to_chunks: {e}")
            import traceback
            logger.error(f"📋 Stack trace: {traceback.format_exc()}")
            
            # Se parse_xml_dump não retornou nada, vamos verificar o arquivo
            if processed == 0:
                logger.error("🔍 Debugging: parse_xml_dump retornou 0 artigos")
                try:
                    # Tentar parsing direto para debug
                    logger.error(f"🔍 Tentando debug direto do arquivo: {filepath}")
                    debug_count = 0
                    for debug_article in self.parse_xml_dump(filepath):
                        debug_count += 1
                        logger.error(f"🔍 Debug encontrou artigo {debug_count}: {debug_article.title}")
                        if debug_count >= 3:
                            break
                    logger.error(f"🔍 Debug final: {debug_count} artigos encontrados")
                except Exception as debug_e:
                    logger.error(f"🔍 Erro no debug: {debug_e}")
    
    def _split_into_chunks(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Divide texto em chunks por parágrafos"""
        # Dividir por parágrafos duplos
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Se adicionar o parágrafo ultrapassar o limite, finalizar chunk atual
            if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Adicionar último chunk se não estiver vazio
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_chunk_size]]

# Instância global
wikipedia_dump_processor = WikipediaDumpProcessor()