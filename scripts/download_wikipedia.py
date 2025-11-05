"""
Script para baixar e processar dumps da Wikipedia

Suporta:
- Wikipedia em Português (ptwiki)
- Simple English Wikipedia (simplewiki)
- Processamento automático de BZ2/XML
- Ingestão no Qdrant via LangChain
"""

import os
import sys
import logging
import requests
from pathlib import Path
from typing import Optional

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.langchainWikipediaService import (
    langchain_wikipedia_service,
    WikipediaDocument
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WikipediaDumpDownloader:
    """Gerenciador de downloads de dumps da Wikipedia"""
    
    DUMP_URLS = {
        'pt': 'https://dumps.wikimedia.org/ptwiki/latest/ptwiki-latest-pages-articles.xml.bz2',
        'simple': 'https://dumps.wikimedia.org/simplewiki/latest/simplewiki-latest-pages-articles.xml.bz2',
        'en': 'https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2'
    }
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
    
    def download_dump(self, language: str = 'pt', max_size_gb: Optional[float] = None) -> Path:
        """
        Baixa dump da Wikipedia
        
        Args:
            language: 'pt', 'simple' ou 'en'
            max_size_gb: Tamanho máximo em GB (None = sem limite)
        
        Returns:
            Path do arquivo baixado
        """
        if language not in self.DUMP_URLS:
            raise ValueError(f"Linguagem inválida. Use: {list(self.DUMP_URLS.keys())}")
        
        url = self.DUMP_URLS[language]
        filename = f"{language}wiki-latest-pages-articles.xml.bz2"
        filepath = self.data_dir / filename
        
        logger.info(f"📥 Iniciando download: {url}")
        logger.info(f"💾 Salvando em: {filepath}")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            total_gb = total_size / (1024**3)
            
            logger.info(f"📊 Tamanho total: {total_gb:.2f} GB")
            
            if max_size_gb and total_gb > max_size_gb:
                raise Exception(f"Arquivo muito grande ({total_gb:.2f} GB > {max_size_gb} GB)")
            
            # Download com progress
            downloaded = 0
            chunk_size = 8192
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress a cada 100MB
                        if downloaded % (100 * 1024 * 1024) == 0:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"⬇️ Progress: {progress:.1f}% ({downloaded/(1024**3):.2f} GB)")
            
            logger.info(f"✅ Download concluído: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Erro no download: {e}")
            if filepath.exists():
                filepath.unlink()
            raise
    
    def process_dump(self, dump_path: Path, max_articles: int = 1000) -> int:
        """
        Processa dump e ingere no Qdrant
        
        Args:
            dump_path: Caminho do arquivo BZ2/XML
            max_articles: Número máximo de artigos a processar
        
        Returns:
            Número de chunks ingeridos
        """
        logger.info(f"📄 Processando dump: {dump_path}")
        logger.info(f"📊 Limite: {max_articles} artigos")
        
        try:
            # Inicializar serviço LangChain
            langchain_wikipedia_service.inicializar()
            
            # Usar o processador de dumps
            from services.wikipediaDumpService import wikipedia_dump_processor
            
            # Parse do dump XML
            wiki_docs = []
            articles_processed = 0
            
            logger.info(f"🔄 Iniciando parse do dump...")
            
            for article in wikipedia_dump_processor.parse_xml_dump(str(dump_path)):
                if articles_processed >= max_articles:
                    break
                
                # Pular redirecionamentos
                if article.redirect:
                    continue
                
                # Criar WikipediaDocument
                wiki_doc = WikipediaDocument(
                    title=article.title,
                    content=article.content,
                    url=f"https://simple.wikipedia.org/wiki/{article.title.replace(' ', '_')}",
                    metadata={
                        'source': 'wikipedia_dump',
                        'language': 'simple',
                        'article_id': str(article.id),
                        'timestamp': article.timestamp
                    }
                )
                wiki_docs.append(wiki_doc)
                articles_processed += 1
                
                # Log a cada 100 artigos
                if articles_processed % 100 == 0:
                    logger.info(f"📊 Processados: {articles_processed} artigos")
            
            logger.info(f"📚 {len(wiki_docs)} documentos extraídos")
            
            # Ingerir no Qdrant via LangChain
            if wiki_docs:
                chunks_count = langchain_wikipedia_service.ingerir_documentos(wiki_docs)
                logger.info(f"✅ Processamento concluído: {chunks_count} chunks")
                return chunks_count
            else:
                logger.warning("⚠️ Nenhum documento foi extraído")
                return 0
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download e processamento de dumps da Wikipedia')
    parser.add_argument('--language', '-l', 
                       choices=['pt', 'simple', 'en'],
                       default='simple',
                       help='Linguagem da Wikipedia (default: simple)')
    parser.add_argument('--max-articles', '-m',
                       type=int,
                       default=1000,
                       help='Número máximo de artigos (default: 1000)')
    parser.add_argument('--max-size-gb', '-s',
                       type=float,
                       help='Tamanho máximo do dump em GB')
    parser.add_argument('--skip-download', '-sd',
                       action='store_true',
                       help='Pular download (usar arquivo existente)')
    parser.add_argument('--data-dir', '-d',
                       default='./data',
                       help='Diretório de dados (default: ./data)')
    
    args = parser.parse_args()
    
    downloader = WikipediaDumpDownloader(data_dir=args.data_dir)
    
    # Download
    if not args.skip_download:
        logger.info(f"🌍 Baixando Wikipedia {args.language}...")
        dump_path = downloader.download_dump(
            language=args.language,
            max_size_gb=args.max_size_gb
        )
    else:
        dump_path = Path(args.data_dir) / f"{args.language}wiki-latest-pages-articles.xml.bz2"
        if not dump_path.exists():
            logger.error(f"❌ Arquivo não encontrado: {dump_path}")
            return
        logger.info(f"📂 Usando arquivo existente: {dump_path}")
    
    # Processar
    logger.info(f"⚙️ Processando dump...")
    chunks = downloader.process_dump(dump_path, max_articles=args.max_articles)
    
    logger.info(f"🎉 Concluído! {chunks} chunks ingeridos no Qdrant")


if __name__ == '__main__':
    main()
