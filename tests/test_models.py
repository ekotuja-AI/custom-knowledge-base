"""
Testes unitários para os modelos de dados
"""
import pytest
from api.models import (
    WikipediaResultModel,
    RAGResponseModel,
    StatusResponse,
    AdicionarArtigoRequest,
    PerguntarRequest,
    BuscarRequest
)


class TestWikipediaResultModel:
    """Testes para o modelo WikipediaResultModel"""
    
    def test_criar_result_minimo(self):
        """Testa criação de WikipediaResultModel com campos mínimos"""
        result = WikipediaResultModel(
            title="Test Article",
            content="Test content",
            url="https://test.com",
            score=0.85
        )
        
        assert result.title == "Test Article"
        assert result.content == "Test content"
        assert result.url == "https://test.com"
        assert result.score == 0.85
    
    def test_result_score_range(self):
        """Testa se o score está em um range válido"""
        result = WikipediaResultModel(
            title="Test",
            content="Content",
            url="url",
            score=0.5
        )
        
        assert 0.0 <= result.score <= 1.0


class TestRAGResponseModel:
    """Testes para o modelo RAGResponseModel"""
    
    def test_criar_rag_response(self):
        """Testa criação de RAGResponseModel"""
        sources = [
            WikipediaResultModel(
                title="Source 1",
                content="Content 1",
                url="url1",
                score=0.9
            )
        ]
        
        response = RAGResponseModel(
            pergunta="What is AI?",
            resposta="AI is artificial intelligence",
            fontes=sources,
            raciocinio="Found 1 source"
        )
        
        assert response.pergunta == "What is AI?"
        assert response.resposta == "AI is artificial intelligence"
        assert len(response.fontes) == 1
        assert response.fontes[0].title == "Source 1"
        assert response.raciocinio == "Found 1 source"
    
    def test_rag_response_sem_sources(self):
        """Testa RAGResponseModel sem fontes"""
        response = RAGResponseModel(
            pergunta="Unknown question",
            resposta="No information found",
            fontes=[],
            raciocinio="No sources"
        )
        
        assert len(response.fontes) == 0


class TestStatusResponse:
    """Testes para o modelo StatusResponse"""
    
    def test_status_response_ok(self):
        """Testa StatusResponse com sistema funcionando"""
        status = StatusResponse(
            status="ok",
            qdrant_conectado=True,
            colecoes=2,
            modelo_embedding_carregado=True,
            text_splitter_configurado=True,
            openai_configurado=False,
            inicializado=True
        )
        
        assert status.status == "ok"
        assert status.qdrant_conectado is True
        assert status.colecoes == 2
        assert status.inicializado is True
    
    def test_status_response_degraded(self):
        """Testa StatusResponse com sistema degradado"""
        status = StatusResponse(
            status="degraded",
            qdrant_conectado=False,
            colecoes=0,
            modelo_embedding_carregado=True,
            text_splitter_configurado=True,
            openai_configurado=False,
            inicializado=True
        )
        
        assert status.status == "degraded"
        assert status.qdrant_conectado is False


class TestRequestModels:
    """Testes para modelos de requisição"""
    
    def test_adicionar_artigo_request(self):
        """Testa AdicionarArtigoRequest"""
        request = AdicionarArtigoRequest(titulo="Python")
        
        assert request.titulo == "Python"
    
    def test_perguntar_request_minimo(self):
        """Testa PerguntarRequest com campos mínimos"""
        request = PerguntarRequest(pergunta="O que é Python?")
        
        assert request.pergunta == "O que é Python?"
        assert request.max_chunks == 5  # valor padrão
    
    def test_perguntar_request_com_max_chunks(self):
        """Testa PerguntarRequest com max_chunks customizado"""
        request = PerguntarRequest(
            pergunta="O que é Python?",
            max_chunks=5
        )
        
        assert request.pergunta == "O que é Python?"
        assert request.max_chunks == 5
    
    def test_buscar_request(self):
        """Testa BuscarRequest"""
        request = BuscarRequest(
            query="inteligência artificial",
            limit=10
        )
        
        assert request.query == "inteligência artificial"
        assert request.limit == 10
    
    def test_buscar_request_default_limit(self):
        """Testa BuscarRequest com limit padrão"""
        request = BuscarRequest(query="test")
        
        assert request.query == "test"
        assert request.limit == 10  # default

