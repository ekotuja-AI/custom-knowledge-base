"""
Testes de configuração e variáveis de ambiente
"""
import pytest
import os
from api.config import APIConfig


class TestAPIConfig:
    """Testes para configurações da aplicação"""
    
    def test_api_config_exists(self):
        """Testa existência da classe APIConfig"""
        assert APIConfig is not None
        assert hasattr(APIConfig, 'TITLE')
        assert hasattr(APIConfig, 'VERSION')
    
    def test_api_config_values(self):
        """Testa valores da configuração da API"""
        assert APIConfig.TITLE == "Dicionário Vetorial API"
        assert APIConfig.VERSION == "1.0.0"
        assert APIConfig.HOST == "0.0.0.0"
        assert APIConfig.PORT == 9000
    
    def test_api_description(self):
        """Testa descrição da API"""
        assert hasattr(APIConfig, 'DESCRIPTION')
        assert len(APIConfig.DESCRIPTION) > 50
        assert isinstance(APIConfig.DESCRIPTION, str)


class TestEnvironmentVariables:
    """Testes relacionados a variáveis de ambiente"""
    
    def test_qdrant_host_default(self):
        """Testa valor padrão de QDRANT_HOST"""
        # Se não estiver definido, deve usar valor padrão
        default_host = os.getenv("QDRANT_HOST", "localhost")
        
        assert isinstance(default_host, str)
        assert len(default_host) > 0
    
    def test_qdrant_port_default(self):
        """Testa valor padrão de QDRANT_PORT"""
        default_port = int(os.getenv("QDRANT_PORT", "6333"))
        
        assert isinstance(default_port, int)
        assert default_port > 0
    
    def test_ollama_host_default(self):
        """Testa valor padrão de OLLAMA_HOST"""
        default_host = os.getenv("OLLAMA_HOST", "ollama")
        
        assert isinstance(default_host, str)
        assert len(default_host) > 0
    
    def test_ollama_port_default(self):
        """Testa valor padrão de OLLAMA_PORT"""
        default_port = int(os.getenv("OLLAMA_PORT", "11434"))
        
        assert isinstance(default_port, int)
        assert default_port > 0
    
    def test_llm_model_default(self):
        """Testa valor padrão de LLM_MODEL"""
        default_model = os.getenv("LLM_MODEL", "qwen2.5:7b")
        
        assert isinstance(default_model, str)
        assert ":" in default_model  # Formato esperado: nome:versão
    
    def test_embedding_model_default(self):
        """Testa valor padrão de EMBEDDING_MODEL"""
        default_model = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        
        assert isinstance(default_model, str)
        assert len(default_model) > 0
