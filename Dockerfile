FROM python:3.9-slim

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# Criar e definir o diretório de trabalho
WORKDIR /app

# Copiar arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código fonte
COPY . .

# Executar o script de configuração
RUN python setup_config.py

# Criar diretórios necessários
RUN mkdir -p examples results temp

# Definir o comando padrão
ENTRYPOINT ["python", "scripts_modulares/DAMICORE_Pareto_script.py"]
