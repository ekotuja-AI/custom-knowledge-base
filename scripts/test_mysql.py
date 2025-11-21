import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.environ.get("MYSQL_HOST", "mysql"),
    user=os.environ.get("MYSQL_USER", "root"),
    password=os.environ.get("MYSQL_PASSWORD", "root"),
    database=os.environ.get("MYSQL_DATABASE", "customkb"),
    port=int(os.environ.get("MYSQL_PORT", "3306"))
)

cursor = conn.cursor()
cursor.execute("SHOW TABLES;")
tables = cursor.fetchall()
print("Tabelas no banco:")
for t in tables:
    print("-", t[0])
cursor.close()
conn.close()
print("Conexão MySQL OK!")
