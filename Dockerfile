# Use Python 3.11 for better performance and latest features
FROM python:3.11-slim

# Configurar variáveis de ambiente para otimização
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Configurar variáveis específicas para DAMICORE
ENV DAMICORE_TIMEOUT=7200
ENV DAMICORE_CHUNK_SIZE=500
ENV DAMICORE_BOOTSTRAP_SAMPLES=2

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libc6-dev \
    gzip \
    bzip2 \
    xz-utils \
    git \
    curl \
    wget \
    build-essential \
    pkg-config \
    libhdf5-dev \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar e definir o diretório de trabalho
WORKDIR /app

# Atualizar pip para a versão mais recente
RUN pip install --upgrade pip setuptools wheel

# Copiar arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar dependências Python com otimizações
RUN pip install --no-cache-dir --compile -r requirements.txt

# Copiar o código fonte
COPY . .

# Criar diretórios necessários para o pipeline DAMICORE
RUN mkdir -p \
    examples \
    results \
    temp \
    data \
    config \
    damicore_analysis \
    external_drive \
    logs

# Configurar permissões adequadas
RUN chmod +x src/scripts/*.py

# Criar usuário não-root para segurança
RUN groupadd -r damicore && useradd -r -g damicore damicore
RUN chown -R damicore:damicore /app
USER damicore

# Definir ponto de saúde para monitoramento
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Labels para metadados da imagem
LABEL maintainer="DAMICORE Team" \
      version="2.0" \
      description="DAMICORE Pipeline with Resume Functionality and Ultra-Large File Support" \
      python.version="3.11" \
      features="checkpoint,resume,streaming,ultra-large-files"

# Comando padrão - script otimizado para arquivos grandes
ENTRYPOINT ["python", "src/scripts/DAMICORE_Pareto_script_chunks_external.py"]
