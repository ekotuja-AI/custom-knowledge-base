FROM python:3.10-slim

# Instalar dependências do sistema para processamento XML e NLP
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar PyTorch CPU primeiro para evitar dependências CUDA
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copiar requirements e instalar dependências
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir --timeout=1000 -r requirements_minimal.txt

# Criar diretório para dados
RUN mkdir -p /app/data

# Copiar código da aplicação
COPY . .

# Expor porta da API
EXPOSE 9000

# Comando padrão para API principal com LangChain
CMD ["uvicorn", "api.wikipediaFuncionalAPI:app", "--host", "0.0.0.0", "--port", "9000"]