#!/usr/bin/env python3
"""
Script para reprocessar TODOS os artigos existentes no Qdrant
com a nova Parse API que retorna conteúdo completo da Wikipedia
"""
import requests
import time
from collections import defaultdict

def listar_artigos_unicos():
    """Lista todos os títulos únicos no Qdrant"""
    try:
        print("📋 Listando artigos no Qdrant...")
        
        response = requests.post(
            'http://qdrant:6333/collections/wikipedia_langchain/points/scroll',
            json={
                "limit": 10000,
                "with_payload": True,
                "with_vector": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            points = data.get('result', {}).get('points', [])
            
            # Extrair títulos únicos
            titulos = set()
            chunks_por_titulo = defaultdict(int)
            
            for point in points:
                titulo = point.get('payload', {}).get('title', '')
                if titulo:
                    titulos.add(titulo)
                    chunks_por_titulo[titulo] += 1
            
            print(f"✅ Total de artigos únicos: {len(titulos)}")
            print(f"✅ Total de chunks: {len(points)}")
            
            return sorted(titulos), chunks_por_titulo
        else:
            print(f"❌ Erro ao listar artigos: {response.status_code}")
            return [], {}
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return [], {}

def reprocessar_artigo(titulo):
    """Reprocessa um artigo específico"""
    try:
        print(f"   📝 {titulo}...", end=" ", flush=True)
        
        response = requests.post(
            'http://localhost:9000/adicionar',
            json={'titulo': titulo},
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            chunks = data.get('chunks_adicionados', 0)
            print(f"✅ {chunks} chunks")
            return True, chunks
        else:
            print(f"❌ Erro {response.status_code}")
            return False, 0
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout")
        return False, 0
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        return False, 0

def main():
    print("=" * 80)
    print("🔄 REPROCESSAMENTO DE TODOS OS ARTIGOS COM PARSE API")
    print("=" * 80)
    
    # Listar artigos existentes
    titulos, chunks_antigos = listar_artigos_unicos()
    
    if not titulos:
        print("\n⚠️ Nenhum artigo encontrado para reprocessar")
        return
    
    print(f"\n📊 Primeiros 15 artigos a reprocessar:")
    for titulo in titulos[:15]:
        chunks = chunks_antigos[titulo]
        status = "📉 RESUMO" if chunks <= 3 else "✅ OK"
        print(f"   {status} {titulo} ({chunks} chunks)")
    
    if len(titulos) > 15:
        print(f"   ... e mais {len(titulos) - 15} artigos")
    
    # Contar artigos com poucos chunks (provavelmente só resumo)
    artigos_resumo = sum(1 for t in titulos if chunks_antigos[t] <= 3)
    print(f"\n⚠️  {artigos_resumo} artigos com ≤3 chunks (provavelmente só resumo)")
    print(f"📊 {len(titulos) - artigos_resumo} artigos com >3 chunks (conteúdo completo)")
    
    print(f"\n🔄 Isso irá reprocessar TODOS os {len(titulos)} artigos.")
    print("   ⏱️  Tempo estimado: ~{:.0f} minutos".format(len(titulos) * 2 / 60))
    
    # Reprocessar
    print("\n" + "=" * 80)
    print("🚀 INICIANDO REPROCESSAMENTO")
    print("=" * 80)
    
    sucessos = 0
    falhas = 0
    total_chunks_novos = 0
    melhorias = 0
    tempo_inicio = time.time()
    
    for i, titulo in enumerate(titulos, 1):
        print(f"[{i}/{len(titulos)}]", end=" ")
        
        chunks_antes = chunks_antigos[titulo]
        sucesso, chunks = reprocessar_artigo(titulo)
        
        if sucesso:
            sucessos += 1
            total_chunks_novos += chunks
            if chunks > chunks_antes * 2:  # Melhorou significativamente
                melhorias += 1
                print(f"      📈 {chunks_antes} → {chunks} chunks (+{chunks - chunks_antes})")
        else:
            falhas += 1
        
        # Pausa entre artigos
        if i < len(titulos):
            time.sleep(0.5)
    
    tempo_total = time.time() - tempo_inicio
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DO REPROCESSAMENTO")
    print("=" * 80)
    print(f"✅ Sucessos: {sucessos}/{len(titulos)}")
    print(f"❌ Falhas: {falhas}")
    print(f"📈 Melhorias significativas: {melhorias} artigos")
    print(f"📦 Total de novos chunks: {total_chunks_novos}")
    print(f"⏱️  Tempo total: {tempo_total:.1f}s ({tempo_total/60:.1f} min)")
    print(f"⚡ Velocidade: {len(titulos)/(tempo_total/60):.1f} artigos/min")
    print("=" * 80)
    
    print("\n✅ Reprocessamento concluído!")
    print("💡 Teste agora buscas por termos específicos dos artigos")

if __name__ == "__main__":
    main()
