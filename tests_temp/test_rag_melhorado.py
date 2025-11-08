#!/usr/bin/env python3
"""
Teste do sistema RAG melhorado
"""
import requests
import json
import time

print("=" * 70)
print("🧪 TESTANDO SISTEMA RAG MELHORADO")
print("=" * 70)

# Teste 1: Pergunta sobre IA
print("\n📋 TESTE 1: Pergunta sobre Inteligência Artificial")
print("-" * 70)

start = time.time()
response = requests.post(
    'http://localhost:9000/perguntar',
    json={
        'pergunta': 'O que é inteligência artificial e como funciona?',
        'max_chunks': 5
    },
    timeout=120
)
elapsed = time.time() - start

if response.status_code == 200:
    data = response.json()
    
    print(f"\n✅ Status: {response.status_code}")
    print(f"⏱️ Tempo: {elapsed:.1f}s")
    print(f"\n📝 PERGUNTA:\n{data['pergunta']}")
    print(f"\n🤖 RESPOSTA:\n{data['resposta']}")
    print(f"\n📚 FONTES USADAS: {len(data['fontes'])} documentos")
    for i, fonte in enumerate(data['fontes'], 1):
        print(f"   {i}. {fonte['title']} (score: {fonte['score']:.3f})")
    print(f"\n⚙️ RACIOCÍNIO: {data['raciocinio']}")
    
    # Avaliar qualidade
    resposta = data['resposta']
    print(f"\n📊 ANÁLISE DA RESPOSTA:")
    print(f"   - Tamanho: {len(resposta)} caracteres")
    print(f"   - Em português: {'✅' if any(c in resposta for c in ['ç', 'ã', 'õ', 'é', 'á']) else '⚠️'}")
    print(f"   - Usa contexto: {'✅' if len(data['fontes']) > 0 else '❌'}")
    print(f"   - Detalhada: {'✅' if len(resposta) > 200 else '⚠️ Muito curta'}")
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.text)

# Teste 2: Pergunta sobre ciência
print("\n\n📋 TESTE 2: Pergunta sobre Ciência")
print("-" * 70)

start = time.time()
response = requests.post(
    'http://localhost:9000/perguntar',
    json={
        'pergunta': 'Como a ciência usa lógica e evidências?',
        'max_chunks': 3
    },
    timeout=120
)
elapsed = time.time() - start

if response.status_code == 200:
    data = response.json()
    
    print(f"\n✅ Status: {response.status_code}")
    print(f"⏱️ Tempo: {elapsed:.1f}s")
    print(f"\n📝 PERGUNTA:\n{data['pergunta']}")
    print(f"\n🤖 RESPOSTA:\n{data['resposta']}")
    print(f"\n📚 FONTES: {len(data['fontes'])} documentos")
    
    resposta = data['resposta']
    print(f"\n📊 Tamanho da resposta: {len(resposta)} caracteres")
else:
    print(f"❌ Erro: {response.status_code}")

print("\n" + "=" * 70)
print("✅ TESTES CONCLUÍDOS")
print("=" * 70)
