from qdrant_client import QdrantClient

client = QdrantClient(host='qdrant', port=6333)
info = client.get_collection('wikipedia_langchain')
print(f'Total de pontos: {info.points_count}')

result = client.scroll(collection_name='wikipedia_langchain', limit=1, with_vectors=True)
if result[0]:
    vector = result[0][0].vector[:10]
    print(f'Primeiros 10 valores do vetor: {vector}')
    
    # Testar busca
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    query = "África"
    query_vector = model.encode(query).tolist()
    print(f'\nBuscando por: {query}')
    print(f'Primeiros 10 valores do query vector: {query_vector[:10]}')
    
    # Busca sem threshold
    search_result = client.search(
        collection_name='wikipedia_langchain',
        query_vector=query_vector,
        limit=5
    )
    
    print(f'\nResultados da busca (sem threshold):')
    for i, hit in enumerate(search_result, 1):
        print(f'{i}. {hit.payload.get("title")} - Score: {hit.score:.4f}')
        print(f'   Conteúdo: {hit.payload.get("content")[:100]}...')
else:
    print('Nenhum ponto encontrado')
