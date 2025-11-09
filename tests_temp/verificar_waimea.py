#!/usr/bin/env python3
from qdrant_client import QdrantClient

client = QdrantClient(host='qdrant_offline', port=6333)

print("\n=== WIKIPEDIA_LANGCHAIN ===")
points_lc = client.scroll(collection_name='wikipedia_langchain', limit=20)[0]
for p in points_lc:
    title = p.payload.get('metadata', {}).get('title', 'Sem título')
    print(f"  - {title} (id: {p.id})")

print(f"\nTotal: {len(points_lc)} documentos")

print("\n=== WIKIPEDIA_OFFLINE ===")
points_off = client.scroll(collection_name='wikipedia_offline', limit=20)[0]
for p in points_off:
    title = p.payload.get('title', 'Sem título')
    print(f"  - {title} (id: {p.id})")

print(f"\nTotal: {len(points_off)} documentos")

# Buscar especificamente por Waimea
print("\n=== BUSCA POR 'WAIMEA' ===")
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
query_vector = model.encode("Waimea")

results_lc = client.search(
    collection_name='wikipedia_langchain',
    query_vector=query_vector,
    limit=10
)

print("\nLangChain collection:")
for r in results_lc:
    title = r.payload.get('metadata', {}).get('title', 'Sem título')
    print(f"  - {title}: {r.score:.4f}")

results_off = client.search(
    collection_name='wikipedia_offline',
    query_vector=query_vector,
    limit=10
)

print("\nOffline collection:")
for r in results_off:
    title = r.payload.get('title', 'Sem título')
    print(f"  - {title}: {r.score:.4f}")
