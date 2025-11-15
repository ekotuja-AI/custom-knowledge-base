META_RESPONSES = {
    "identidade": "Sou um sistema de perguntas e respostas offline baseado em artigos da Wikipedia, utilizando LangChain, Qdrant e Ollama.",
    "modelo_arquitetura": "Utilizo o modelo LLM '{model_name}' via Ollama, com LangChain para processamento semântico e Qdrant como banco vetorial. O backend é Python, e todo o conhecimento é limitado aos artigos cadastrados.",
    "ollama": "Sim, utilizo Ollama para gerar respostas usando modelos LLM.",
    "langchain": "Sim, utilizo LangChain para processamento semântico e busca de artigos.",
    "qdrant": "Sim, utilizo Qdrant como banco vetorial para armazenar e buscar os artigos.",
    "wikipedia": "Sim, os artigos cadastrados são extraídos da Wikipedia.",
    "funcionamento": "O sistema funciona buscando artigos cadastrados da Wikipedia, processando-os com LangChain e armazenando em Qdrant. As respostas são geradas por um modelo LLM via Ollama, sempre limitadas ao conteúdo dos artigos presentes na base."
}
