import requests
import json

# Teste 1: Busca por África
print("=" * 80)
print("TESTE 1: Busca por 'África'")
print("=" * 80)
response = requests.post('http://localhost:9000/perguntar', 
                         json={'pergunta': 'Me cite 3 países da África', 'max_chunks': 5})
result = response.json()
print(f"Pergunta: {result['question']}")
print(f"\nResposta: {result['answer']}")
print(f"\nFontes encontradas: {len(result['sources'])}")
for i, source in enumerate(result['sources'][:3], 1):
    print(f"\n{i}. {source['title']} (score: {source['score']:.4f})")
    print(f"   {source['content'][:150]}...")

# Teste 2: Busca por computador
print("\n" + "=" * 80)
print("TESTE 2: Busca por 'O que é um computador?'")
print("=" * 80)
response = requests.post('http://localhost:9000/perguntar', 
                         json={'pergunta': 'O que é um computador?', 'max_chunks': 5})
result = response.json()
print(f"Pergunta: {result['question']}")
print(f"\nResposta: {result['answer']}")
print(f"\nFontes encontradas: {len(result['sources'])}")
for i, source in enumerate(result['sources'][:3], 1):
    print(f"\n{i}. {source['title']} (score: {source['score']:.4f})")
    print(f"   {source['content'][:150]}...")
