from fastapi import APIRouter, Query
from services.dbService import (
    listar_usuarios,
    get_or_create_user,
    listar_bases,
    listar_tudo,
    listar_embeddings,
    buscar_dimensao_embedding
)
from .models import User

router = APIRouter()

@router.get("/dbService/embedding_dimensao")
def get_embedding_dimensao(nome: str = Query(...)):
    dim = buscar_dimensao_embedding(nome)
    return {"dimensao": dim}

@router.get("/dbService/users")
def users():
    return listar_usuarios()

@router.post("/dbService/users/{email}")
def user(email: str):
    return get_or_create_user(email)

@router.post("/dbService/login", response_model=User)
async def login(email: str):
    user = get_or_create_user(email)
    return User(**user)

@router.get("/dbService/bases")
def bases():
    return listar_bases()

@router.get("/dbService/all")
def tudo():
    return listar_tudo()

@router.get("/dbService/embeddings")
def embeddings():
    print("API: Listando modelos de embedding...")
    return listar_embeddings()