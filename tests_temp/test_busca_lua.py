#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

client = QdrantClient(host='qdrant_offline', port=6333)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

query = "lua"
query_vector = model.encode(query).tolist()

print(f"\n=== BUSCA POR '{query}' ===\n")

results = client.search(
    collection_name='wikipedia_langchain',
    query_vector=query_vector,
    limit=10,
    score_threshold=0.0
)

for i, r in enumerate(results):
    title = r.payload.get('title', 'Sem título')
    score = r.score
    content = r.payload.get('content', '')[:100]
    print(f"{i+1}. {title}: {score:.4f}")
    print(f"   {content}...\n")
