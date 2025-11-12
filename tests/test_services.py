"""
Testes unitários para funções auxiliares e utilidades
"""
import pytest
from services.wikipediaOfflineService import WikipediaOfflineService


class TestTextProcessing:
    """Testes para processamento de texto"""
    
    def test_dividir_em_chunks_texto_curto(self):
        """Testa divisão de texto curto em chunks"""
        service = WikipediaOfflineService()
        texto = "Este é um texto curto."
        
        chunks = service._dividir_em_chunks(texto, max_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0] == texto
    
    def test_dividir_em_chunks_texto_longo(self):
        """Testa divisão de texto longo em chunks"""
        service = WikipediaOfflineService()
        
        # Criar texto longo com múltiplos parágrafos
        paragrafo = "Este é um parágrafo de teste. " * 50  # ~1500 chars
        texto = f"{paragrafo}\n\n{paragrafo}"
        
        chunks = service._dividir_em_chunks(texto, max_size=1000)
        
        # Verifica que chunks foram criados
        assert len(chunks) > 0
        # Cada chunk deve ter conteúdo
        for chunk in chunks:
            assert len(chunk) > 0
    
    def test_dividir_em_chunks_paragrafos_multiplos(self):
        """Testa divisão respeitando parágrafos"""
        service = WikipediaOfflineService()
        
        texto = "Parágrafo 1\n\nParágrafo 2\n\nParágrafo 3"
        chunks = service._dividir_em_chunks(texto, max_size=50)
        
        assert len(chunks) >= 1
        # Cada chunk não deve estar vazio
        for chunk in chunks:
            assert len(chunk.strip()) > 0
    
    def test_dividir_em_chunks_texto_vazio(self):
        """Testa divisão de texto vazio"""
        service = WikipediaOfflineService()
        texto = ""
        
        chunks = service._dividir_em_chunks(texto)
        
        assert len(chunks) == 0


class TestServiceInitialization:
    """Testes para inicialização de serviços"""
    
    def test_wikipedia_offline_service_init(self):
        """Testa inicialização do WikipediaOfflineService"""
        service = WikipediaOfflineService()
        assert service.collection_name == "wikipedia_langchain"
        assert service.ollama_host == "ollama"
        assert service.ollama_port == 11434
        assert service.model_name == "qwen2.5:7b"
        assert service._initialized is False
    
    def test_service_config_from_env(self):
        """Testa se o serviço lê configurações corretas"""
        service = WikipediaOfflineService()
        
        # Verificar valores padrão
        assert isinstance(service.ollama_port, int)
        assert service.model_name.startswith("qwen")


class TestSearchResultProcessing:
    """Testes para processamento de resultados de busca"""
    
    def test_get_sample_results_retorna_lista(self):
        """Testa se _get_sample_results retorna lista"""
        service = WikipediaOfflineService()
        
        results = service._get_sample_results("test query", limit=3)
        
        assert isinstance(results, list)
        assert len(results) <= 3
    
    def test_get_sample_results_contem_fallback(self):
        """Testa se resultados de exemplo contêm mensagem de fallback"""
        service = WikipediaOfflineService()
        
        results = service._get_sample_results("test query", limit=5)
        
        # O sistema agora retorna lista vazia para evitar respostas inventadas
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_sample_results_tem_scores(self):
        """Testa se resultados de exemplo têm scores válidos"""
        service = WikipediaOfflineService()
        
        results = service._get_sample_results("AI", limit=3)
        
        for result in results:
            assert hasattr(result, 'score')
            assert 0.0 <= result.score <= 1.0


class TestOllamaConnection:
    """Testes para conexão com Ollama (sem fazer requests reais)"""
    
    def test_test_ollama_connection_retorna_bool(self):
        """Testa se _test_ollama_connection retorna boolean"""
        service = WikipediaOfflineService()
        
        # Método deve retornar True ou False
        result = service._test_ollama_connection()
        
        assert isinstance(result, bool)


class TestStatistics:
    """Testes para obtenção de estatísticas"""
    
    def test_obter_estatisticas_retorna_dict(self):
        """Testa se obter_estatisticas retorna dicionário"""
        service = WikipediaOfflineService()
        
        stats = service.obter_estatisticas()
        
        assert isinstance(stats, dict)
        assert "sistema_offline" in stats
    
    def test_estatisticas_sem_conexao(self):
        """Testa estatísticas quando não há conexão"""
        service = WikipediaOfflineService()
        # Sem inicializar, client será None
        
        stats = service.obter_estatisticas()
        
        assert "colecao" in stats or "erro" in stats


class TestVerificarStatus:
    """Testes para verificação de status do sistema"""
    
    def test_verificar_status_retorna_dict(self):
        """Testa se verificar_status retorna dicionário"""
        service = WikipediaOfflineService()
        
        status = service.verificar_status()
        
        assert isinstance(status, dict)
        assert "status" in status
        assert "qdrant_conectado" in status
        assert "inicializado" in status
    
    def test_verificar_status_campos_obrigatorios(self):
        """Testa se todos os campos obrigatórios estão presentes"""
        service = WikipediaOfflineService()
        
        status = service.verificar_status()
        
        required_fields = [
            "status",
            "qdrant_conectado",
            "colecoes",
            "modelo_embedding_carregado",
            "text_splitter_configurado",
            "openai_configurado",
            "inicializado"
        ]
        
        for field in required_fields:
            assert field in status
    
    def test_status_types(self):
        """Testa tipos dos campos de status"""
        service = WikipediaOfflineService()
        
        status = service.verificar_status()
        
        assert isinstance(status["status"], str)
        assert isinstance(status["qdrant_conectado"], bool)
        assert isinstance(status["colecoes"], int)
        assert isinstance(status["inicializado"], bool)
