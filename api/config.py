"""
Configurações da API do Custom Knowledge Base

Este módulo contém as configurações centralizadas da aplicação.
"""

import os
from typing import Dict, Any


class APIConfig:
    """Configurações da API"""
    
    # Informações da API
    TITLE = "Custom Knowledge Base API"
    VERSION = "1.0.0"
    DESCRIPTION = """
    **API REST para busca semântica em dicionário usando embeddings e Qdrant**
    
    Esta API utiliza modelos de linguagem avançados (SentenceTransformers) para permitir 
    buscas semânticas em um dicionário de palavras. É possível:
    
    * **Buscar palavras** por similaridade semântica
    * **Adicionar novas palavras** ao dicionário
    * **Consultar estatísticas** da base de dados
    * **Monitorar status** dos serviços
    
    ## Tecnologias Utilizadas
    
    * **FastAPI**: Framework web moderno e rápido
    * **Qdrant**: Banco de dados vetorial para busca semântica
    * **SentenceTransformers**: Modelo multilíngue para embeddings
    * **Docker**: Containerização e orquestração
    
    ## Como Usar
    
    1. Use `/buscar` para encontrar palavras semanticamente similares
    2. Use `/adicionar` para expandir o dicionário
    3. Use `/status` para verificar a saúde do sistema
    4. Use `/estatisticas` para métricas da base de dados
    """
    
    # Configurações do servidor
    HOST = "0.0.0.0"
    PORT = 9000
    RELOAD = True
    
    # Informações de contato
    CONTACT_INFO = {
        "name": "Eduardo Kotujansky",
        "url": "https://github.com/ekotuja-AI",
        "email": "ekotuja@gmail.com",
    }
    
    # Informações de licença
    LICENSE_INFO = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    # Tags para documentação
    OPENAPI_TAGS = [
        {
            "name": "Busca",
            "description": "Operações de busca semântica no dicionário",
        },
        {
            "name": "Gestão",
            "description": "Adicionar e gerenciar palavras no dicionário",
        },
        {
            "name": "Sistema",
            "description": "Monitoramento e informações do sistema",
        },
    ]

    @classmethod
    def get_fastapi_config(cls) -> Dict[str, Any]:
        """Retorna configuração completa para FastAPI"""
        return {
            "title": cls.TITLE,
            "description": cls.DESCRIPTION,
            "version": cls.VERSION,
            "terms_of_service": "https://opensource.org/licenses/MIT",
            "contact": cls.CONTACT_INFO,
            "license_info": cls.LICENSE_INFO,
            "openapi_tags": cls.OPENAPI_TAGS,
        }
