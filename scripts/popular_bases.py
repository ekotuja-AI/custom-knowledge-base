import mysql.connector
import os
from services.wikipediaOfflineService import wikipedia_offline_service

wikipedia_offline_service.inicializar()
qdrant_client = wikipedia_offline_service.client

conn = mysql.connector.connect(
    host=os.environ.get("MYSQL_HOST", "mysql"),
    user=os.environ.get("MYSQL_USER", "root"),
    password=os.environ.get("MYSQL_PASSWORD", "root"),
    database=os.environ.get("MYSQL_DATABASE", "customkb"),
    port=int(os.environ.get("MYSQL_PORT", "3306"))
)
cursor = conn.cursor()

collections = qdrant_client.get_collections().collections

for col in collections:
    nome = col.name
    cursor.execute("""
        INSERT IGNORE INTO knowledge_bases (nome, usuario_id, qdrant_collection)
        VALUES (%s, %s, %s)
    """, (nome, 1, nome))  # usuario_id=1 padrão, ajuste conforme necessário

conn.commit()
cursor.close()
conn.close()
print("Coleções do Qdrant populadas na tabela knowledge_bases!")
