#!/usr/bin/env python3
"""
Script para adicionar artigos da Wikipedia ao sistema
"""
import requests
import time

# Lista de artigos que você quer adicionar (em português ou inglês)
ARTIGOS = [
    # Tecnologia
    "Python (programming language)",
    "Artificial intelligence",
    "Machine learning",
    "Deep learning",
    "Neural network",
    
    # Ciência
    "Physics",
    "Chemistry",
    "Biology",
    "Mathematics",
    "Computer science",
    
    # História
    "World War II",
    "Ancient Rome",
    "Renaissance",
    
    # Geografia
    "Brazil",
    "United States",
    "Europe",
    
    # Adicione mais aqui...
]

def adicionar_artigo(titulo):
    """Adiciona um artigo ao sistema"""
    try:
        print(f"\n📄 Adicionando: {titulo}")
        
        response = requests.post(
            'http://localhost:9000/adicionar',
            json={'titulo': titulo},
            timeout=300  # 5 minutos
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Sucesso! {data.get('chunks_adicionados', 0)} chunks criados")
            return True
        else:
            print(f"   ❌ Erro: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout - artigo muito grande ou processamento lento")
        return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("=" * 70)
    print("🚀 ADICIONANDO ARTIGOS DA WIKIPEDIA")
    print("=" * 70)
    
    sucessos = 0
    falhas = 0
    
    for i, artigo in enumerate(ARTIGOS, 1):
        print(f"\n[{i}/{len(ARTIGOS)}]")
        
        if adicionar_artigo(artigo):
            sucessos += 1
        else:
            falhas += 1
        
        # Pequena pausa entre artigos
        if i < len(ARTIGOS):
            time.sleep(2)
    
    print("\n" + "=" * 70)
    print(f"✅ Sucessos: {sucessos}")
    print(f"❌ Falhas: {falhas}")
    print(f"📊 Total processado: {len(ARTIGOS)} artigos")
    print("=" * 70)
    
    # Verificar estatísticas finais
    print("\n📊 Estatísticas do sistema:")
    try:
        response = requests.get('http://localhost:9000/estatisticas')
        if response.status_code == 200:
            stats = response.json()
            print(f"   Total de chunks: {stats.get('total_chunks', 0)}")
            print(f"   Coleções: {stats.get('collections', [])}")
    except:
        pass

if __name__ == "__main__":
    main()
