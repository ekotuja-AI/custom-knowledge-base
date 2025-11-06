#!/usr/bin/env python3
"""
Script para listar artigos da Wikipedia armazenados no Qdrant
"""

import requests
import json
from collections import Counter

def listar_artigos_qdrant(
    host="localhost",
    port=6333,
    collection="wikipedia_langchain",
    output_file=None
):
    """
    Lista todos os artigos únicos do Qdrant
    
    Args:
        host: Host do Qdrant
        port: Porta do Qdrant
        collection: Nome da coleção
        output_file: Arquivo para salvar a lista (opcional)
    """
    
    url = f"http://{host}:{port}/collections/{collection}/points/scroll"
    
    all_titles = []
    offset = None
    
    print(f"🔍 Buscando artigos da coleção '{collection}'...")
    
    while True:
        # Preparar payload
        payload = {
            "limit": 1000,
            "with_payload": True,
            "with_vector": False
        }
        
        if offset:
            payload["offset"] = offset
        
        # Fazer requisição
        response = requests.post(url, json=payload)
        data = response.json()
        
        # Extrair títulos
        points = data.get("result", {}).get("points", [])
        titles = [point["payload"].get("title", "") for point in points]
        all_titles.extend(titles)
        
        print(f"  Processados: {len(all_titles)} chunks...")
        
        # Verificar se há mais páginas
        offset = data.get("result", {}).get("next_page_offset")
        if not offset:
            break
    
    # Obter títulos únicos
    unique_titles = sorted(set(all_titles))
    
    # Estatísticas
    title_counts = Counter(all_titles)
    
    print(f"\n✅ Processamento concluído!")
    print(f"📊 Total de chunks: {len(all_titles)}")
    print(f"📚 Artigos únicos: {len(unique_titles)}")
    print(f"📈 Média de chunks por artigo: {len(all_titles) / len(unique_titles):.1f}")
    
    # Top 10 artigos com mais chunks
    print(f"\n🏆 Top 10 artigos com mais chunks:")
    for title, count in title_counts.most_common(10):
        print(f"  {count:3d} chunks - {title}")
    
    # Primeiros 50 artigos
    print(f"\n📋 Primeiros 50 artigos (alfabeticamente):")
    for i, title in enumerate(unique_titles[:50], 1):
        print(f"  {i:2d}. {title}")
    
    # Salvar em arquivo se especificado
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for title in unique_titles:
                f.write(f"{title}\n")
        print(f"\n💾 Lista salva em: {output_file}")
    
    return unique_titles


def exportar_json(titles, output_file="artigos.json"):
    """Exporta lista em formato JSON com estatísticas"""
    data = {
        "total_artigos": len(titles),
        "artigos": titles,
        "data_exportacao": "2025-11-06"
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 JSON exportado: {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Lista artigos da Wikipedia no Qdrant")
    parser.add_argument("--host", default="localhost", help="Host do Qdrant")
    parser.add_argument("--port", type=int, default=6333, help="Porta do Qdrant")
    parser.add_argument("--collection", default="wikipedia_langchain", help="Nome da coleção")
    parser.add_argument("--output", help="Arquivo de saída (.txt)")
    parser.add_argument("--json", help="Exportar como JSON")
    
    args = parser.parse_args()
    
    # Listar artigos
    titles = listar_artigos_qdrant(
        host=args.host,
        port=args.port,
        collection=args.collection,
        output_file=args.output
    )
    
    # Exportar JSON se solicitado
    if args.json:
        exportar_json(titles, args.json)
