import mysql.connector
import time

class MySQLService:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'root',
            'database': 'customkb'
        }

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def get_or_create_user(self, email):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            cursor.execute("INSERT INTO users (email, criado_em) VALUES (%s, NOW())", (email,))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    def create_knowledge_base(self, email, nome):
        user = self.get_or_create_user(email)
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        qdrant_collection = f"base_{user['id']}_{nome}"
        cursor.execute("INSERT INTO knowledge_bases (nome, usuario_id, qdrant_collection, criado_em) VALUES (%s, %s, %s, NOW())", (nome, user['id'], qdrant_collection))
        conn.commit()
        cursor.execute("SELECT * FROM knowledge_bases WHERE usuario_id=%s AND nome=%s", (user['id'], nome))
        base = cursor.fetchone()
        cursor.close()
        conn.close()
        return base

    def register_telemetry(self, evento, dados, usuario_id=None, colecao=None, tipo=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO telemetria (evento, dados, usuario_id, colecao, tipo, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (evento, str(dados), usuario_id, colecao, tipo, time.strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        cursor.close()
        conn.close()

# Exemplo de uso:
# mysql_service = MySQLService()
# mysql_service.register_telemetry('adicionar_artigo', {'titulo': 'Python', 'chunks': 10}, usuario_id=1, colecao='wikipedia_langchain', tipo='ingestao')
