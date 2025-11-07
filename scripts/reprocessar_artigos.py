"""
Script para reprocessar artigos existentes com embeddings corretos
"""
import sys
import os
sys.path.insert(0, '/app')

from services.langchainWikipediaService import langchain_wikipedia_service
from services.langchainWikipediaService import WikipediaDocument
import wikipediaapi
from tqdm import tqdm
import time

def reprocessar_artigos(arquivo_lista: str, host: str = "localhost"):
    """Reprocessa artigos da lista"""
    
    # Configurar Wikipedia API
    wiki = wikipediaapi.Wikipedia(
        language='pt',
        user_agent='WikipediaRAG/1.0 (ekotuja@gmail.com)'
    )
    
    # Inicializar serviço
    print("🚀 Inicializando LangChain Wikipedia Service...")
    langchain_wikipedia_service.inicializar()
    
    # Ler lista de artigos
    print(f"\n📖 Lendo artigos de {arquivo_lista}...")
    with open(arquivo_lista, 'r', encoding='utf-8') as f:
        titulos = [linha.strip() for linha in f if linha.strip()]
    
    print(f"✅ {len(titulos)} artigos encontrados\n")
    
    # Processar artigos
    documentos = []
    erros = 0
    
    for i, titulo in enumerate(tqdm(titulos, desc="📥 Baixando artigos"), 1):
        try:
            page = wiki.page(titulo)
            
            if not page.exists():
                print(f"\n⚠️  Artigo não encontrado: {titulo}")
                erros += 1
                continue
            
            # Criar documento
            doc = WikipediaDocument(
                title=page.title,
                content=page.text,
                url=page.fullurl,
                metadata={
                    'language': 'pt',
                    'categories': list(page.categories.keys())[:5]
                }
            )
            documentos.append(doc)
            
            # Ingerir em lotes de 50
            if len(documentos) >= 50:
                chunks = langchain_wikipedia_service.ingerir_documentos(documentos)
                print(f"\n✅ Lote processado: {chunks} chunks")
                documentos = []
                time.sleep(1)  # Evitar rate limit
                
        except Exception as e:
            print(f"\n❌ Erro ao processar {titulo}: {e}")
            erros += 1
    
    # Processar últimos documentos
    if documentos:
        chunks = langchain_wikipedia_service.ingerir_documentos(documentos)
        print(f"\n✅ Último lote: {chunks} chunks")
    
    # Estatísticas finais
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS FINAIS")
    print("="*60)
    stats = langchain_wikipedia_service.obter_estatisticas()
    print(f"Total de pontos: {stats.get('total_points', 0)}")
    print(f"Artigos processados: {len(titulos) - erros}")
    print(f"Erros: {erros}")
    print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Reprocessar artigos da Wikipedia')
    parser.add_argument('--input', required=True, help='Arquivo com lista de títulos')
    parser.add_argument('--host', default='localhost', help='Host do Qdrant')
    
    args = parser.parse_args()
    
    reprocessar_artigos(args.input, args.host)
