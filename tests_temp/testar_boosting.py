import requests
import json

# Testar busca
print("=" * 60)
print("TESTE 1: Busca por 'lua'")
print("=" * 60)
response = requests.post(
    "http://localhost:9000/buscar",
    json={"query": "lua"},
    headers={"Content-Type": "application/json"}
)
data = response.json()
print(f"Total de resultados: {data['total_resultados']}")
for i, r in enumerate(data['resultados'], 1):
    print(f"\n{i}. {r['title']} - Score: {r['score']:.4f}")
    print(f"   URL: {r['url']}")
    print(f"   Conteúdo: {r['content'][:150]}...")

print("\n" + "=" * 60)
print("TESTE 2: Busca por 'python'")
print("=" * 60)
response = requests.post(
    "http://localhost:9000/buscar",
    json={"query": "python"},
    headers={"Content-Type": "application/json"}
)
data = response.json()
print(f"Total de resultados: {data['total_resultados']}")
for i, r in enumerate(data['resultados'], 1):
    print(f"\n{i}. {r['title']} - Score: {r['score']:.4f}")
    print(f"   URL: {r['url']}")

print("\n" + "=" * 60)
print("TESTE 3: Busca por 'terra'")
print("=" * 60)
response = requests.post(
    "http://localhost:9000/buscar",
    json={"query": "terra"},
    headers={"Content-Type": "application/json"}
)
data = response.json()
print(f"Total de resultados: {data['total_resultados']}")
for i, r in enumerate(data['resultados'], 1):
    print(f"\n{i}. {r['title']} - Score: {r['score']:.4f}")
    print(f"   URL: {r['url']}")

print("\n" + "=" * 60)
print("TESTE 4: RAG - Pergunta sobre lua")
print("=" * 60)
response = requests.post(
    "http://localhost:9000/perguntar",
    json={"pergunta": "O que é a lua?"},
    headers={"Content-Type": "application/json"}
)
data = response.json()
print(f"Resposta: {data['answer'][:300]}...")
print(f"\nFontes: {data['sources']}")
