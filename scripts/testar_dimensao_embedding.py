import mysql.connector

conn = mysql.connector.connect(
    host='mysql_kb',
    user='root',
    password='root',
    database='customkb'
)
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT nome, dimensao FROM embedding_models WHERE nome = 'paraphrase-multilingual-MiniLM-L12-v2'")
row = cursor.fetchone()
print(row)
cursor.close()
conn.close()
