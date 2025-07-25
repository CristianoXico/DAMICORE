# Docker DAMICORE v2.1 - File Slicer Processor

## 🐳 Visão Geral

O Docker DAMICORE v2.1 está configurado para executar o **DAMICORE_File_Slicer_Processor.py** como script principal, oferecendo:

- ✅ **Processamento automático de arquivos grandes** (fatiamento em chunks de 100 linhas)
- ✅ **Visualizações corrigidas** com nomes originais das variáveis
- ✅ **Dimensionamento adaptativo** para datasets com 100+ variáveis
- ✅ **Sistema de checkpoint/retomada** automático
- ✅ **Suporte a drive externo** para resultados
- ✅ **Pipeline completo** integrado

## 🚀 Execução Rápida

### Comando Básico
```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

### Com Drive Externo
```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v /path/to/external/drive:/app/external_drive \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

### Modo Interativo (Recomendado)
```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest /bin/bash
```

Dentro do container:
```bash
python src/scripts/DAMICORE_File_Slicer_Processor.py
```

## 📁 Estrutura de Volumes

| Volume Host | Volume Container | Descrição |
|-------------|------------------|-----------|
| `./data` | `/app/data` | Arquivos CSV de entrada |
| `./results` | `/app/results` | Resultados do processamento |
| `/external/drive` | `/app/external_drive` | Drive externo (opcional) |

## 🔧 Configuração Avançada

### Variáveis de Ambiente
```bash
docker run -it --rm \
  -e DAMICORE_TIMEOUT=7200 \
  -e DAMICORE_CHUNK_SIZE=500 \
  -e DAMICORE_BOOTSTRAP_SAMPLES=2 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

### Recursos de Sistema
```bash
docker run -it --rm \
  --memory=16g \
  --cpus=8 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest
```

## 📊 Funcionalidades do File Slicer

### 1. Detecção Automática de Tamanho
- **Arquivos < 100 linhas**: Processamento direto com DAMICORE_Filograma_script.py
- **Arquivos ≥ 100 linhas**: Fatiamento automático em chunks de 100 linhas

### 2. Visualizações Corrigidas
- **Nomes originais**: Converte 'col_X.txt' para nomes das colunas
- **Dimensões adaptativas**: Ajusta tamanho baseado no número de variáveis
- **Truncamento inteligente**: Evita sobreposição de labels longos

### 3. Sistema de Checkpoint
- **Retomada automática**: Continua do ponto de interrupção
- **Progresso detalhado**: Acompanha fatias processadas/falhadas
- **Validação robusta**: Verifica integridade dos resultados

## 🎯 Exemplos de Uso

### Exemplo 1: Dataset Pequeno (< 100 linhas)
```bash
# Coloque seu arquivo em ./data/small_dataset.csv
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest

# Resultado: Processamento direto, visualizações em ./results/
```

### Exemplo 2: Dataset Grande (≥ 100 linhas)
```bash
# Coloque seu arquivo em ./data/large_dataset.csv
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  -v /media/external:/app/external_drive \
  damicore:latest

# Resultado: Fatiamento automático, visualizações por fatia
```

### Exemplo 3: Retomada de Processamento
```bash
# Se o processamento foi interrompido, execute novamente
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  damicore:latest

# O sistema detecta automaticamente o checkpoint e continua
```

## 📋 Estrutura de Saída

```
results/
├── dataset_name_sliced_results/
│   ├── slices/
│   │   ├── slice_0001/
│   │   │   ├── damicore_results/          # Arquivos newick
│   │   │   ├── cloud_tree.pdf             # Visualização cloud tree
│   │   │   ├── consensus_tree.pdf         # Visualização consensus
│   │   │   └── tree_biopython.png         # Visualização biopython
│   │   └── slice_0002/
│   │       └── ...
│   ├── compiled_results/                  # Resultados compilados
│   └── file_slicer_checkpoint.json        # Checkpoint do pipeline
```

## 🛠️ Troubleshooting

### Problema: Visualizações vazias
**Solução**: Verificar se as dependências estão instaladas:
```bash
docker exec -it container_name python -c "import toytree, matplotlib; print('OK')"
```

### Problema: Falta de espaço
**Solução**: Usar drive externo:
```bash
docker run -it --rm \
  -v /large/external/drive:/app/external_drive \
  damicore:latest
```

### Problema: Timeout em datasets grandes
**Solução**: Aumentar timeout:
```bash
docker run -it --rm \
  -e DAMICORE_TIMEOUT=14400 \
  damicore:latest
```

## 🔄 Atualização

Para atualizar para a versão mais recente:
```bash
./update-docker.sh
```

## 📞 Suporte

- **Logs**: Verifique os logs do container com `docker logs container_name`
- **Debug**: Execute em modo interativo para debug detalhado
- **Checkpoint**: Verifique o arquivo `file_slicer_checkpoint.json` para status do progresso

---

**DAMICORE v2.1** - Pipeline otimizado com visualizações corrigidas e suporte a datasets ultra-grandes
