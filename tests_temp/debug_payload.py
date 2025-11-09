#!/usr/bin/env python3
from qdrant_client import QdrantClient

client = QdrantClient(host='qdrant_offline', port=6333)

print("\n=== PAYLOADS DOS DOCUMENTOS ===")
points = client.scroll(collection_name='wikipedia_langchain', limit=5, with_payload=True, with_vectors=False)[0]

for i, p in enumerate(points):
    print(f"\n[{i+1}] ID: {p.id}")
    print(f"Payload keys: {list(p.payload.keys())}")
    print(f"Title: {p.payload.get('title', 'NÃO ENCONTRADO')}")
    print(f"Content preview: {p.payload.get('content', '')[:100]}...")
    if 'doc_metadata' in p.payload:
        print(f"Doc metadata: {p.payload['doc_metadata']}")
