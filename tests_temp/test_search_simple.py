from services.langchainWikipediaService import langchain_wikipedia_service

# Inicializar
langchain_wikipedia_service.inicializar()

# Teste 1: África
print("=" * 80)
print("TESTE: Busca por 'África'")
print("=" * 80)
results = langchain_wikipedia_service.buscar_documentos("África", limit=5, score_threshold=0.5)
print(f"Encontrou {len(results)} resultados\n")
for i, result in enumerate(results, 1):
    print(f"{i}. {result.title} (score: {result.score:.4f})")
    print(f"   {result.content[:150]}...\n")

# Teste 2: Computador
print("=" * 80)
print("TESTE: Busca por 'computador'")
print("=" * 80)
results = langchain_wikipedia_service.buscar_documentos("computador", limit=5, score_threshold=0.5)
print(f"Encontrou {len(results)} resultados\n")
for i, result in enumerate(results, 1):
    print(f"{i}. {result.title} (score: {result.score:.4f})")
    print(f"   {result.content[:150]}...\n")

# Teste 3: Continentes
print("=" * 80)
print("TESTE: Busca por 'continentes'")
print("=" * 80)
results = langchain_wikipedia_service.buscar_documentos("continentes", limit=5, score_threshold=0.5)
print(f"Encontrou {len(results)} resultados\n")
for i, result in enumerate(results, 1):
    print(f"{i}. {result.title} (score: {result.score:.4f})")
    print(f"   {result.content[:150]}...\n")
