#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Conectar
client = QdrantClient(host='qdrant_offline', port=6333)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Testar diferentes queries
queries = [
    "Waimea?",
    "Waimea",
    "o que é Waimea?",
    "o que é Waimea (Havaí)?",
    "Havaí"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: '{query}'")
    print('='*60)
    
    # Gerar embedding
    query_vector = model.encode(query).tolist()
    
    # Buscar com threshold baixo
    results = client.search(
        collection_name='wikipedia_langchain',
        query_vector=query_vector,
        limit=5,
        score_threshold=0.0  # Sem threshold
    )
    
    for i, r in enumerate(results):
        title = r.payload.get('title', 'Sem título')
        score = r.score
        content_preview = r.payload.get('content', '')[:80]
        print(f"  [{i+1}] {title}: {score:.4f}")
        print(f"      {content_preview}...")
