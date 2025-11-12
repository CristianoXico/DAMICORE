# 🐳 Docker DAMICORE — Guia Completo

**Versão Atual:** 2.1  
**Python:** 3.11  
**Última Atualização:** 12 de novembro de 2025

---

## 📋 Visão Geral

O Docker DAMICORE é um container otimizado para executar análises filogenéticas em datasets de **qualquer tamanho**, com suporte a:

- ✅ **Processamento de arquivos grandes** (fatiamento automático em chunks)
- ✅ **Sistema de checkpoint/retomada** (continuar após interrupções)
- ✅ **Visualizações corrigidas** (nomes de variáveis originais)
- ✅ **Dimensionamento adaptativo** (datasets com 100+ variáveis)
- ✅ **Suporte a drive externo** (armazenamento em mídia externa)
- ✅ **Execução segura** (usuário não-root)
- ✅ **Pipeline completo** (entrada → processamento → visualizações)

---

## 🚀 Guia Rápido

### 1. Construir a Imagem Docker

```bash
# Build simples
docker build -t damicore:latest .

# Ou usar o script fornecido
./build-docker.sh
```

### 2. Executar o Pipeline

#### Opção A: Usar Docker Run Direto

```bash
# Básico
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest

# Com drive externo
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v /caminho/para/drive/externo:/app/external_drive \
  -v $(pwd)/results:/app/results \
  damicore:latest

# Modo interativo (shell)
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest /bin/bash
```

#### Opção B: Usar Docker Compose

```bash
# Iniciar
docker-compose up

# Parar
docker-compose down

# Ver logs
docker-compose logs -f

# Shell interativo
docker-compose exec damicore /bin/bash
```

### 3. Verificar Resultados

Após a execução, os resultados estão em `./results/`:

```
results/
├── dataset_name_sliced_results/
│   ├── slices/
│   │   ├── slice_0001/
│   │   │   ├── damicore_results/     # Arquivos Newick
│   │   │   ├── cloud_tree.pdf        # Visualização Cloud Tree
│   │   │   ├── consensus_tree.pdf    # Visualização Consensus
│   │   │   └── tree_biopython.png    # Visualização BioPython
│   │   └── slice_0002/
│   │       └── ...
│   └── compiled_results/             # Resultados compilados
```

---

## 🔧 Configuração

### Variáveis de Ambiente

Configure o comportamento do pipeline via variáveis de ambiente:

```bash
# Timeout para processamento (em segundos)
-e DAMICORE_TIMEOUT=7200           # Padrão: 2 horas

# Tamanho de chunk para fatiamento
-e DAMICORE_CHUNK_SIZE=500         # Padrão: 500 linhas

# Amostras de bootstrap
-e DAMICORE_BOOTSTRAP_SAMPLES=2    # Padrão: 2
```

### Perfis de Tamanho de Arquivo

Escolha configurações baseado no tamanho do seu dataset:

#### 📊 Arquivos Pequenos (< 1 GB / < 100 linhas)

```bash
docker run -it --rm \
  -e DAMICORE_CHUNK_SIZE=2000 \
  -e DAMICORE_BOOTSTRAP_SAMPLES=5 \
  -e DAMICORE_TIMEOUT=3600 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

**Características:**
- Processamento direto sem fatiamento
- Mais amostras de bootstrap para melhor análise
- Timeout curto (1 hora)

#### 📊 Arquivos Médios (1-10 GB / 100-1000 linhas)

```bash
docker run -it --rm \
  -e DAMICORE_CHUNK_SIZE=500 \
  -e DAMICORE_BOOTSTRAP_SAMPLES=3 \
  -e DAMICORE_TIMEOUT=7200 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

**Características:**
- Configuração padrão recomendada
- Bom equilíbrio entre qualidade e velocidade
- Timeout de 2 horas

#### 📊 Arquivos Grandes (> 10 GB / > 1000 linhas)

```bash
docker run -it --rm \
  -e DAMICORE_CHUNK_SIZE=100 \
  -e DAMICORE_BOOTSTRAP_SAMPLES=2 \
  -e DAMICORE_TIMEOUT=14400 \
  -v $(pwd)/data:/app/data \
  -v /caminho/para/drive/externo:/app/external_drive \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

**Características:**
- Fatiamento agressivo (chunks menores)
- Menos bootstrap mas processamento mais rápido
- Timeout longo (4 horas)
- **Requer drive externo** para armazenar intermediários

### Recursos de Sistema

Controle CPU e memória alocados ao container:

```bash
docker run -it --rm \
  --memory=16g \
  --cpus=8 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

**Recomendações:**
- **Mínimo:** 2 GB RAM, 1 CPU
- **Recomendado:** 8-16 GB RAM, 4-8 CPUs
- **Ideal:** 32+ GB RAM, 16+ CPUs (para ultra-grandes)

---

## 📁 Volumes e Mapeamento

| Caminho Host | Caminho Container | Permissão | Descrição |
|---|---|---|---|
| `./data` | `/app/data` | RW | Arquivos CSV de entrada |
| `./results` | `/app/results` | RW | Resultados do processamento |
| `./external_drive` | `/app/external_drive` | RW | Drive externo para grandes datasets |
| `./logs` | `/app/logs` | RW | Logs da execução |
| `./config` | `/app/config` | RO | Arquivos de configuração |

### Exemplo com Todos os Volumes

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/external_drive:/app/external_drive \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config:ro \
  damicore:latest
```

---

## 🎯 Exemplos de Uso

### Exemplo 1: Dataset Padrão

```bash
# Preparar diretório
mkdir -p data results
cp seu_arquivo.csv data/

# Executar
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest

# Verificar resultados
ls -la results/
```

### Exemplo 2: Múltiplos Datasets

```bash
# Colocar múltiplos arquivos em ./data/
cp arquivo1.csv arquivo2.csv arquivo3.csv data/

# Executar — processará automaticamente todos
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

### Exemplo 3: Retomada após Interrupção

```bash
# Pipeline foi interrompido
# Executar novamente — sistema detecta checkpoint e continua
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest

# Verifica pipeline_progress.json e retoma
```

### Exemplo 4: Processamento com Drive Externo

```bash
# Para datasets ultra-grandes
docker run -it --rm \
  -e DAMICORE_CHUNK_SIZE=50 \
  -e DAMICORE_TIMEOUT=28800 \
  -v $(pwd)/data:/app/data \
  -v /media/external/damicore:/app/external_drive \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

---

## 🔄 Scripts Disponíveis

### build-docker.sh

Constrói a imagem Docker com otimizações:

```bash
./build-docker.sh

# Opções
./build-docker.sh --no-cache    # Build completo sem cache
./build-docker.sh --test        # Build + teste de funcionalidade
```

### deploy-docker.sh

Script auxiliar para gerenciar containers:

```bash
./deploy-docker.sh up           # Iniciar pipeline
./deploy-docker.sh down         # Parar pipeline
./deploy-docker.sh logs         # Ver logs
./deploy-docker.sh shell        # Abrir shell no container
./deploy-docker.sh status       # Status e recursos usados
./deploy-docker.sh restart      # Reiniciar
./deploy-docker.sh clean        # Limpar containers e volumes
```

---

## 🛠️ Troubleshooting

### Problema: Build Falha

**Erro:** `ERROR: failed to solve with frontend dockerfile.v0`

**Solução:**
```bash
# Limpar sistema Docker
docker system prune -f

# Reconstruir com verbosidade
docker build --no-cache -t damicore:latest .
```

### Problema: Visualizações Vazias

**Erro:** Arquivos PDF/PNG gerados mas vazios

**Solução:**
```bash
# Verificar dependências de visualização
docker run -it damicore:latest python -c \
  "import toytree, matplotlib, plotly; print('Visualizações OK')"

# Se falhar, reconstruir imagem
./build-docker.sh --no-cache
```

### Problema: Memória Insuficiente

**Erro:** `MemoryError` ou `Killed`

**Solução:**
```bash
# Aumentar limite de memória
docker run -it --rm \
  --memory=32g \
  -e DAMICORE_CHUNK_SIZE=50 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest

# Ou usar drive externo para swapping
docker run -it --rm \
  --memory=16g \
  -v /caminho/para/drive/externo:/app/external_drive \
  damicore:latest
```

### Problema: Timeout

**Erro:** `TimeoutError` ou processamento interrompido

**Solução:**
```bash
# Aumentar timeout
docker run -it --rm \
  -e DAMICORE_TIMEOUT=28800 \
  -e DAMICORE_CHUNK_SIZE=100 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

### Problema: Permissões em Resultados

**Erro:** `Permission denied` ao acessar resultados

**Solução:**
```bash
# Ajustar permissões após execução
sudo chown -R $USER:$USER ./results ./logs ./external_drive

# Ou executar docker com permissões do usuário
docker run -it --rm \
  --user $(id -u):$(id -g) \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

---

## 📊 Monitoramento

### Ver Logs em Tempo Real

```bash
# Terminal 1: Iniciar pipeline
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest

# Terminal 2: Ver logs
docker logs -f <container_id>

# Ou com docker-compose
docker-compose logs -f
```

### Verificar Recursos

```bash
# Ver uso de CPU e memória
docker stats <container_id>

# Ou com docker-compose
docker-compose stats
```

### Verificar Checkpoint

```bash
# Dentro do container
cat /app/results/pipeline_progress.json | python -m json.tool

# Ou do host
docker exec <container_id> cat /app/results/pipeline_progress.json
```

---

## 🔐 Segurança

### Características de Segurança

- ✅ **Executa como usuário não-root** (`damicore`)
- ✅ **Volumes de entrada read-only** (quando possível)
- ✅ **Rede isolada** (sem acesso externo por padrão)
- ✅ **Healthchecks configurados** (detecta travamentos)
- ✅ **Sem credenciais hardcoded** (use variáveis de ambiente)

### Boas Práticas

```bash
# ❌ Evitar: Rodar como root
docker run -it --user root damicore:latest

# ✅ Correto: Especificar usuário
docker run -it --user damicore damicore:latest

# ❌ Evitar: Volumes sem restrição
-v /etc:/app/etc

# ✅ Correto: Volumes específicos
-v $(pwd)/data:/app/data:ro
-v $(pwd)/results:/app/results:rw
```

---

## 🚀 Otimizações

### Cache de Dependências

Docker implementa cache automático de camadas:

```dockerfile
# Camada 1: Dependências do SO (cacheia bem)
RUN apt-get install ...

# Camada 2: Requirements Python (cacheia bem)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Camada 3: Código (muda frequentemente)
COPY . /app/
```

**Dica:** Quando atualizar código, as duas primeiras camadas reutilizam cache.

### Multi-stage Build (Futuro)

Para versões futuras, considerar multi-stage para reduzir tamanho final:

```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
RUN pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
```

---

## 📚 Referências

### Arquivos Relacionados

- `Dockerfile` — Definição da imagem
- `docker-compose.yml` — Orquestração
- `entrypoint.sh` — Script de inicialização
- `requirements.txt` — Dependências Python
- `.dockerignore` — Arquivos ignorados no build

### Documentação Adicional

- [Docker Official Documentation](https://docs.docker.com/)
- [Python Docker Best Practices](https://docs.docker.com/language/python/)
- [DAMICORE README](./README.md)
- [DAMICORE CONTRIBUTING](./CONTRIBUTING.md)

---

## 📞 Suporte

### Problemas Comuns

1. **Build lento:** Use `--no-cache=false` para reutilizar cache
2. **Imagem grande:** Limpar `/var/lib/apt/lists/` após apt-get
3. **Container lento:** Aumentar `--cpus` e `--memory`

### Logs para Debug

```bash
# Ver histórico completo
docker logs <container_id> --tail=100

# Salvar logs em arquivo
docker logs <container_id> > /tmp/damicore_debug.log 2>&1
```

### Contato

- 📧 Email: support@damicore.dev
- 🐛 Issues: GitHub Issues
- 💬 Discussion: GitHub Discussions

---

**Versão:** 2.1  
**Última Atualização:** 12 de novembro de 2025  
**Mantido por:** DAMICORE Team
