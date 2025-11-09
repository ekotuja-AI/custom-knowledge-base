#!/usr/bin/env python3
"""
Script para testar se o sistema responde sobre artigos específicos
"""
import requests
import json

def testar_pergunta(pergunta, max_chunks=5):
    """Testa uma pergunta e mostra a resposta"""
    print("\n" + "=" * 70)
    print(f"❓ PERGUNTA: {pergunta}")
    print("=" * 70)
    
    try:
        # Fazer pergunta
        response = requests.post(
            'http://localhost:9000/perguntar',
            json={
                'pergunta': pergunta,
                'max_chunks': max_chunks
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n🤖 RESPOSTA:")
            print(data['resposta'])
            
            print(f"\n📚 FONTES USADAS ({len(data['fontes'])}):")
            for i, fonte in enumerate(data['fontes'], 1):
                print(f"   {i}. {fonte['title'][:60]} (score: {fonte['score']:.3f})")
            
            print(f"\n⚙️ {data['raciocinio']}")
            
            # Avaliação
            resposta = data['resposta']
            print(f"\n📊 AVALIAÇÃO:")
            print(f"   ✓ Tamanho: {len(resposta)} caracteres")
            print(f"   ✓ Fontes: {len(data['fontes'])} documentos")
            print(f"   ✓ Score médio: {sum(f['score'] for f in data['fontes'])/len(data['fontes']):.3f}")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def buscar_artigos(query, limit=5):
    """Busca artigos para verificar se estão no sistema"""
    print(f"\n🔍 Buscando artigos sobre: {query}")
    try:
        response = requests.post(
            'http://localhost:9000/buscar',
            json={'query': query, 'limit': limit},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📚 Encontrados {data['total_resultados']} resultados:")
            for i, resultado in enumerate(data['resultados'], 1):
                print(f"   {i}. {resultado['title'][:50]} (score: {resultado['score']:.3f})")
            return True
        else:
            print(f"❌ Erro na busca: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("\n" + "🧪 " * 25)
    print("TESTANDO CONHECIMENTO DO SISTEMA")
    print("🧪 " * 25)
    
    # Teste 1: Verificar se artigos estão no sistema
    print("\n" + "=" * 70)
    print("TESTE 1: Verificando artigos no sistema")
    print("=" * 70)
    buscar_artigos("Python programming", 5)
    buscar_artigos("artificial intelligence", 5)
    buscar_artigos("machine learning", 5)
    
    # Teste 2: Perguntas específicas
    print("\n" + "=" * 70)
    print("TESTE 2: Fazendo perguntas específicas")
    print("=" * 70)
    
    perguntas = [
        "O que é Python e para que serve?",
        "Como funciona machine learning?",
        "Qual a diferença entre inteligência artificial e machine learning?",
        "O que são redes neurais?",
    ]
    
    for pergunta in perguntas:
        testar_pergunta(pergunta, max_chunks=5)
        print("\n" + "-" * 70)

if __name__ == "__main__":
    main()
