"""
Modelos Pydantic para a Wikipedia Semantic Search API

Este módulo contém todas as classes de dados utilizadas pela API,
incluindo modelos de request, response e validação de dados.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from datetime import datetime

# --- MULTIUSUÁRIO ---
class User(BaseModel):
    """Modelo de usuário para autenticação simples por email"""
    id: Optional[int] = Field(None, description="ID do usuário no banco de dados")
    email: str = Field(..., description="Email do usuário", min_length=5, max_length=120, example="usuario@email.com")
    criado_em: Optional[datetime] = Field(None, description="Data de criação do usuário")

class KnowledgeBase(BaseModel):
    """Modelo para base de conhecimento personalizada do usuário"""
    id: Optional[int] = Field(None, description="ID da base no banco de dados")
    nome: str = Field(..., description="Nome da base de conhecimento", min_length=3, max_length=100, example="minha-wiki")
    usuario_id: int = Field(..., description="ID do usuário dono da base")
    qdrant_collection: str = Field(..., description="Nome da coleção no Qdrant para esta base")
    criado_em: Optional[datetime] = Field(None, description="Data de criação da base")


class BuscarRequest(BaseModel):
    """Modelo para requisição de busca semântica"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "inteligência artificial e machine learning",
                "limit": 10
            }
        }
    )
    
    query: str = Field(
        ...,
        description="Termo ou pergunta para buscar nos artigos da Wikipedia",
        min_length=1,
        max_length=500,
        example="inteligência artificial e machine learning"
    )
    limit: Optional[int] = Field(
        default=10,
        description="Número máximo de resultados a retornar",
        ge=1,
        le=50,
        example=10
    )


class AdicionarArtigoRequest(BaseModel):
    """Modelo para adicionar um artigo da Wikipedia"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "titulo": "Ciência de dados"
            }
        }
    )
    
    titulo: str = Field(
        ...,
        description="Título do artigo da Wikipedia para adicionar",
        min_length=1,
        max_length=200,
        example="Ciência de dados"
    )


class PerguntarRequest(BaseModel):
    """Modelo para fazer perguntas com RAG"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pergunta": "O que é inteligência artificial e como funciona?",
                "max_chunks": 10
            }
        }
    )
    
    pergunta: str = Field(
        ...,
        description="Pergunta a ser respondida usando o conhecimento da Wikipedia",
        min_length=1,
        max_length=500,
        example="O que é inteligência artificial e como funciona?"
    )
    max_chunks: Optional[int] = Field(
        default=30,
        description="Número máximo de chunks de contexto para a resposta",
        ge=1,
        le=50,
        example=30
    )


class WikipediaResultModel(BaseModel):
    """Modelo para resultado de busca da Wikipedia"""
    title: str = Field(..., description="Título do artigo da Wikipedia")
    content: str = Field(..., description="Conteúdo relevante do artigo")
    url: str = Field(..., description="URL do artigo original na Wikipedia")
    score: float = Field(
        ...,
        description="Score de similaridade semântica (0-10, maior é melhor, scores >1 indicam match exato no título)",
        ge=0.0,
        le=10.0
    )


class BuscarResponse(BaseModel):
    """Modelo para resposta de busca semântica"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "inteligência artificial",
                "total_resultados": 3,
                "resultados": [
                    {
                        "title": "Inteligência artificial",
                        "content": "Inteligência artificial é a simulação de processos de inteligência humana por máquinas...",
                        "url": "https://pt.wikipedia.org/wiki/Intelig%C3%AAncia_artificial",
                        "score": 0.9234
                    }
                ],
                "tempo_busca_ms": 45.2,
                "telemetria": {
                    "tempo_busca_qdrant_ms": 40.5,
                    "tempo_filtragem_ms": 4.7,
                    "tempo_total_ms": 45.2,
                    "query_length": 23,
                    "limite_solicitado": 10,
                    "resultados_antes_filtro": 15,
                    "resultados_depois_filtro": 3
                }
            }
        }
    )
    
    query: str = Field(..., description="Query original da busca")
    total_resultados: int = Field(..., description="Número total de resultados encontrados")
    resultados: List[WikipediaResultModel] = Field(..., description="Lista de resultados ordenados por relevância")
    tempo_busca_ms: Optional[float] = Field(None, description="Tempo de busca em milissegundos")
    telemetria: Optional[dict] = Field(None, description="Telemetria detalhada da busca semântica")


class RAGResponseModel(BaseModel):
    """Modelo para resposta do sistema RAG"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pergunta": "O que é inteligência artificial?",
                "resposta": "Inteligência artificial (IA) é um campo da ciência da computação que visa criar sistemas capazes de realizar tarefas que normalmente requerem inteligência humana...",
                "fontes": [
                    {
                        "title": "Inteligência artificial",
                        "content": "Conteúdo relevante do artigo...",
                        "url": "https://pt.wikipedia.org/wiki/Intelig%C3%AAncia_artificial",
                        "score": 0.9234
                    }
                ],
                "raciocinio": "Resposta gerada baseada em 3 fontes relevantes da Wikipedia.",
                "tempo_processamento_ms": 1250.5
            }
        }
    )
    
    pergunta: str = Field(..., description="Pergunta original")
    resposta: str = Field(..., description="Resposta gerada pelo LLM baseada no contexto")
    fontes: List[WikipediaResultModel] = Field(..., description="Fontes utilizadas para gerar a resposta")
    raciocinio: str = Field(..., description="Explicação do processo de resposta")
    tempo_processamento_ms: Optional[float] = Field(None, description="Tempo total de processamento")
    total_chunks: Optional[int] = Field(None, description="Total de chunks encontrados")
    total_artigos: Optional[int] = Field(None, description="Total de artigos únicos encontrados")
    telemetria: Optional[dict] = Field(None, description="Telemetria detalhada do LLM (tokens, velocidade, etc)")


class BuscaPreviaResponse(BaseModel):
    """Modelo para resposta de busca prévia (antes de gerar resposta com LLM)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pergunta": "O que é Python?",
                "encontrou_resultados": True,
                "total_chunks": 15,
                "total_artigos": 3,
                "fontes": [],
                "tempo_busca_ms": 125.5,
                "telemetria": {
                    "tempo_embedding_ms": 50.2,
                    "tempo_busca_qdrant_ms": 45.3,
                    "tempo_processamento_ms": 30.0,
                    "tempo_total_ms": 125.5,
                    "query_length": 16,
                    "max_chunks_solicitados": 30,
                    "chunks_encontrados": 15,
                    "artigos_encontrados": 3
                }
            }
        }
    )
    
    pergunta: str = Field(..., description="Pergunta original")
    encontrou_resultados: bool = Field(..., description="Se encontrou resultados relevantes")
    total_chunks: int = Field(..., description="Total de chunks encontrados")
    total_artigos: int = Field(..., description="Total de artigos únicos encontrados")
    fontes: List[WikipediaResultModel] = Field(..., description="Fontes encontradas na busca")
    tempo_busca_ms: float = Field(..., description="Tempo da busca em milissegundos")
    telemetria: Optional[dict] = Field(None, description="Telemetria detalhada da busca semântica")


class AdicionarArtigoResponse(BaseModel):
    """Modelo para resposta de adição de artigo"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Artigo adicionado com sucesso",
                "titulo": "Ciência de dados",
                "url": "https://pt.wikipedia.org/wiki/Ci%C3%AAncia_de_dados",
                "chunks_adicionados": 15
            }
        }
    )
    
    message: str = Field(..., description="Mensagem de confirmação")
    titulo: str = Field(..., description="Título do artigo adicionado")
    url: str = Field(..., description="URL do artigo na Wikipedia")
    chunks_adicionados: int = Field(..., description="Número de chunks criados a partir do artigo")


class StatusResponse(BaseModel):
    """Modelo para resposta de status do sistema"""
    status: str = Field(..., description="Status geral do sistema", example="ok")
    qdrant_conectado: bool = Field(..., description="Se a conexão com Qdrant está ativa")
    colecoes: int = Field(..., description="Número de coleções no Qdrant")
    modelo_embedding_carregado: bool = Field(..., description="Se o modelo de embedding está carregado")
    modelo_embedding_nome: str = Field(..., description="Nome do modelo de embedding em uso")
    text_splitter_configurado: bool = Field(..., description="Se o text splitter está configurado")
    openai_configurado: bool = Field(..., description="Se o cliente OpenAI está configurado")
    inicializado: bool = Field(..., description="Se o serviço foi completamente inicializado")
    ollama_disponivel: bool = Field(..., description="Se o Ollama LLM está disponível")
    modelo_llm: str = Field(..., description="Nome do modelo LLM em uso")


class EstatisticasResponse(BaseModel):
    """Modelo para estatísticas da coleção"""
    nome_colecao: str = Field(..., description="Nome da coleção no Qdrant")
    total_chunks: int = Field(..., description="Total de chunks armazenados")
    artigos_unicos: int = Field(..., description="Número de artigos únicos da Wikipedia")
    dimensoes_vetor: int = Field(..., description="Dimensões dos vetores de embedding")
    distancia: str = Field(..., description="Métrica de distância utilizada")
    llm_disponivel: bool = Field(..., description="Se o LLM está disponível para perguntas")


class InfoResponse(BaseModel):
    """Modelo para informações da API"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Wikipedia Semantic Search API",
                "version": "2.0.0",
                "description": "API para busca semântica em artigos da Wikipedia com LLM integrado",
                "endpoints": {
                    "buscar": "/buscar - Busca semântica em artigos",
                    "perguntar": "/perguntar - Perguntas com RAG",
                    "adicionar": "/adicionar - Adicionar artigo da Wikipedia"
                },
                "features": [
                    "Busca semântica usando embeddings",
                    "Sistema RAG com LLM",
                    "Processamento com LangChain",
                    "Base de conhecimento da Wikipedia"
                ]
            }
        }
    )
    
    message: str = Field(..., description="Mensagem de boas-vindas")
    version: str = Field(..., description="Versão da API")
    description: str = Field(..., description="Descrição da API")
    endpoints: dict = Field(..., description="Lista de endpoints disponíveis")
    features: List[str] = Field(..., description="Funcionalidades disponíveis")