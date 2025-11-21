import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any

# Database connection settings (adjust as needed)
DB_CONFIG = {
    'host': 'mysql_kb',
    'user': 'root',
    'password': 'root',
    'database': 'customkb'
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def listar_usuarios() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_or_create_user(email: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (email) VALUES (%s)", (email,))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def listar_bases() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Filtra coleções removidas (removido_em nulo ou campo inexistente)
    try:
        cursor.execute("SELECT * FROM knowledge_bases WHERE removido_em IS NULL")
    except Exception:
        cursor.execute("SELECT * FROM knowledge_bases")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def listar_tudo() -> Dict[str, Any]:
    return {
        'users': listar_usuarios(),
        'knowledge_bases': listar_bases(),
        'embedding_models': listar_embeddings()
    }

def listar_embeddings() -> List[Dict[str, Any]]:
    print("Listando modelos de embedding...")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM embedding_models")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def buscar_dimensao_embedding(nome: str) -> int:
    nome = nome.strip()
    print(f"buscar_dimensao_embedding dimensão do modelo de embedding para: {nome}")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    print(f"SQL: SELECT dimensao FROM embedding_models WHERE nome = '{nome}'")
    cursor.execute("SELECT dimensao FROM embedding_models WHERE nome = %s", (nome,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row and 'dimensao' in row:
        return row['dimensao']
    return None
