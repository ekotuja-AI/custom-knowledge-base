import mysql.connector
import os
import json

MODELOS_JSON = "static/docs/modelos_disponiveis.json"

conn = mysql.connector.connect(
    host=os.environ.get("MYSQL_HOST", "mysql"),
    user=os.environ.get("MYSQL_USER", "root"),
    password=os.environ.get("MYSQL_PASSWORD", "root"),
    database=os.environ.get("MYSQL_DATABASE", "customkb"),
    port=int(os.environ.get("MYSQL_PORT", "3306"))
)
cursor = conn.cursor()

with open(MODELOS_JSON, encoding="utf-8") as f:
    modelos = json.load(f)

for m in modelos.get("embeddings", []):
    cursor.execute("""
        INSERT INTO embedding_models (nome, descricao, dimensao)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE descricao=VALUES(descricao), dimensao=VALUES(dimensao)
    """, (m["name"], m["desc"], int(next((d for d in m["desc"].split() if d.isdigit()), None))) )

conn.commit()
cursor.close()
conn.close()
print("Modelos de embedding populados na tabela embedding_models!")
