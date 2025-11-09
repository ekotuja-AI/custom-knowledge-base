#!/usr/bin/env python3
from qdrant_client import QdrantClient

client = QdrantClient(host='qdrant_offline', port=6333)
points = client.scroll(collection_name='wikipedia_langchain', limit=100, with_payload=True, with_vectors=False)[0]

lua_points = [p for p in points if p.payload.get('title') == 'Lua']

print(f'\n=== ARTIGO LUA ===')
print(f'Total de chunks: {len(lua_points)}\n')

for i, p in enumerate(lua_points):
    content = p.payload.get('content', '')
    print(f'Chunk {i+1}: {len(content)} caracteres')
    print(f'Preview: {content[:150]}...\n')
