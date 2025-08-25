# DAMICORE - Análise de Dados e Fronteira de Pareto

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-✓-blue.svg)](https://www.docker.com/)

Este projeto implementa um pipeline de análise que combina o método DAMICORE (Data Mining of Code Repositories) com análise de Fronteira de Pareto para exploração e visualização de dados.

## 🌟 Recursos Principais

- **Processamento Eficiente** de grandes conjuntos de dados
- **Visualizações Avançadas** incluindo árvores filogenéticas e matrizes de correlação
- **Análise de Fronteira de Pareto** para otimização multiobjetivo
- **Suporte a Docker** para fácil implantação
- **Processamento em Lotes** para arquivos grandes
- **Mapeamento de Nomes** para variáveis originais
- **Sistema de Checkpoint** para recuperação de falhas

## 🚀 Começando

### Pré-requisitos

- Python 3.8 ou superior
- Docker (opcional, mas recomendado)
- 8GB+ de RAM (16GB+ recomendado para conjuntos de dados grandes)
- 10GB+ de espaço em disco

### Instalação

#### Método 1: Usando Docker (Recomendado)

```bash
# Construir a imagem
./build-docker.sh

# Executar o container
./run.sh /caminho/para/seu/arquivo.csv
```

#### Método 2: Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/CristianoXico/DAMICORE.git
cd DAMICORE
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 📊 Uso Básico

### Processando um Arquivo CSV

```bash
# Usando o script principal
python src/scripts/DAMICORE_File_Slicer_Processor.py /caminho/para/seu/arquivo.csv

# Para arquivos grandes (>1GB), use a versão com processamento em lotes
python src/scripts/DAMICORE_Pareto_script_chunks.py /caminho/para/seu/arquivo.csv
```

### Parâmetros Opcionais

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `--output-dir` | Diretório de saída | `./results` |
| `--chunk-size` | Tamanho do lote para processamento | `1000` |
| `--bootstrap-samples` | Número de amostras bootstrap | `2` |
| `--external-drive` | Usar drive externo para armazenamento | `False` |

## 🏗️ Estrutura do Projeto

```
DAMICORE/
├── config/                  # Arquivos de configuração
├── docs/                    # Documentação adicional
├── examples/                # Exemplos de uso
├── scripts_modulares/       # Módulos auxiliares
├── src/                     # Código-fonte principal
│   ├── scripts/             # Scripts de análise
│   └── tree_simplification.py  # Funções de simplificação de árvores
├── tests/                   # Testes automatizados
├── .gitignore
├── Dockerfile               # Configuração do Docker
├── README.md                # Este arquivo
├── requirements.txt         # Dependências Python
└── run.sh                   # Script de execução
```

## 🔍 Visualizações Geradas

O pipeline gera vários arquivos de visualização, incluindo:

1. **Árvore de Nuvem** (`cloud_tree.pdf`)
2. **Árvore de Consenso** (`consensus_tree.pdf`)
3. **Árvore Filogenética** (`tree_biopython.png`)
4. **Matriz de Correlação** (`correlation_matrix.png`)
5. **Análise de Componentes Principais** (`pca_biplot.png`)
6. **Dendrograma Hierárquico** (`hierarchical_clustering_dendrogram.png`)
7. **Grafo de Correlação** (`correlation_network.png`)

## 🧪 Testes de Desempenho

Antes de executar em produção, recomenda-se testar o desempenho:

```bash
# Testar tamanhos de chunk ideais
python src/scripts/test_chunk_sizes.py /caminho/para/seu/arquivo.csv

# Teste completo de desempenho
python src/scripts/test_damicore_performance.py /caminho/para/seu/arquivo.csv
```

## 🛠️ Desenvolvimento

### Estrutura de Dados

O DAMICORE processa arquivos CSV e gera visualizações baseadas em árvores filogenéticas. O mapeamento de nomes de variáveis é mantido para facilitar a interpretação dos resultados.

### Adicionando Novas Visualizações

1. Crie um novo script em `src/scripts/`
2. Importe as funções necessárias dos módulos existentes
3. Adicione a nova visualização ao pipeline principal
4. Atualize a documentação

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estes passos:

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Adicione suas mudanças (`git add .`)
4. Faça o Commit das suas alterações (`git commit -m 'Add some AmazingFeature'`)
5. Faça o Push para a Branch (`git push origin feature/AmazingFeature`)
6. Abra um Pull Request

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 📞 Contato

Cristiano Xico - [@seu_twitter](https://twitter.com/seu_twitter)

Link do Projeto: [https://github.com/CristianoXico/DAMICORE](https://github.com/CristianoXico/DAMICORE)

---

# DAMICORE - Data Analysis and Pareto Frontier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-✓-blue.svg)](https://www.docker.com/)

## 🌟 Key Features

- **Efficient Processing** of large datasets
- **Advanced Visualizations** including phylogenetic trees and correlation matrices
- **Pareto Frontier Analysis** for multi-objective optimization
- **Docker Support** for easy deployment
- **Batch Processing** for large files
- **Variable Name Mapping** for original column names
- **Checkpoint System** for failure recovery

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Docker (optional but recommended)
- 8GB+ RAM (16GB+ recommended for large datasets)
- 10GB+ disk space

### Installation

#### Method 1: Using Docker (Recommended)

```bash
# Build the image
./build-docker.sh

# Run the container
./run.sh /path/to/your/file.csv
```

#### Method 2: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/CristianoXico/DAMICORE.git
cd DAMICORE
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📊 Basic Usage

### Processing a CSV File

```bash
# Using the main script
python src/scripts/DAMICORE_File_Slicer_Processor.py /path/to/your/file.csv

# For large files (>1GB), use the batch processing version
python src/scripts/DAMICORE_Pareto_script_chunks.py /path/to/your/file.csv
```

### Optional Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--output-dir` | Output directory | `./results` |
| `--chunk-size` | Batch size for processing | `1000` |
| `--bootstrap-samples` | Number of bootstrap samples | `2` |
| `--external-drive` | Use external drive for storage | `False` |

## 🏗️ Project Structure

```
DAMICORE/
├── config/                  # Configuration files
├── docs/                    # Additional documentation
├── examples/                # Usage examples
├── scripts_modulares/       # Helper modules
├── src/                     # Main source code
│   ├── scripts/             # Analysis scripts
│   └── tree_simplification.py  # Tree simplification functions
├── tests/                   # Automated tests
├── .gitignore
├── Dockerfile               # Docker configuration
├── README.md                # This file
├── requirements.txt         # Python dependencies
└── run.sh                   # Execution script
```

## 🔍 Generated Visualizations

The pipeline generates several visualization files, including:

1. **Cloud Tree** (`cloud_tree.pdf`)
2. **Consensus Tree** (`consensus_tree.pdf`)
3. **Phylogenetic Tree** (`tree_biopython.png`)
4. **Correlation Matrix** (`correlation_matrix.png`)
5. **Principal Component Analysis** (`pca_biplot.png`)
6. **Hierarchical Clustering** (`hierarchical_clustering_dendrogram.png`)
7. **Correlation Network** (`correlation_network.png`)

## 🧪 Performance Testing

Before running in production, it's recommended to test performance:

```bash
# Test optimal chunk sizes
python src/scripts/test_chunk_sizes.py /path/to/your/file.csv

# Complete performance test
python src/scripts/test_damicore_performance.py /path/to/your/file.csv
```

## 🛠️ Development

### Data Structure

DAMICORE processes CSV files and generates phylogenetic tree-based visualizations. Variable name mapping is maintained to facilitate result interpretation.

### Adding New Visualizations

1. Create a new script in `src/scripts/`
2. Import necessary functions from existing modules
3. Add the new visualization to the main pipeline
4. Update the documentation

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

Cristiano Xico - [@your_twitter](https://twitter.com/your_twitter)

Project Link: [https://github.com/CristianoXico/DAMICORE](https://github.com/CristianoXico/DAMICORE)

```

## 🧪 Testes de Chunk Size e Otimização de Performance

### Por que testar chunk_size?

Antes de executar o pipeline DAMICORE com arquivos grandes, é **altamente recomendado** executar testes de chunk size para:
- Identificar o tamanho ideal de chunk para seu hardware
- Evitar falhas por falta de memória (OOM - Out of Memory)
- Otimizar o tempo de processamento
- Garantir estabilidade durante execuções longas

### Scripts de Teste Disponíveis

#### 1. Teste Básico de Chunk Size
```bash
# Analisa uso de memória e performance para diferentes chunk_sizes
cd src/scripts
python test_chunk_sizes.py /caminho/para/seu/arquivo.csv
```

**O que este teste faz:**
- Testa chunk_sizes: 100, 500, 1000, 5000, 10000, 50000, 100000, 500000
- Monitora uso de memória (inicial, pico, final)
- Mede performance (linhas processadas por segundo)
- Para automaticamente se detectar risco de OOM
- Fornece recomendações baseadas no tamanho do arquivo

#### 2. Teste Completo de Performance do DAMICORE
```bash
# Testa o pipeline completo com diferentes configurações
python test_damicore_performance.py /caminho/para/seu/arquivo.csv
```

**O que este teste faz:**
- Executa o pipeline DAMICORE completo com diferentes chunk_sizes
- Mede tempo total de execução
- Conta arquivos newick gerados
- Identifica a configuração mais rápida e mais estável

### Exemplo de Resultados

```
🧪 Testando chunk_size = 500
  ✅ Processados: 10 chunks, 5,000 linhas
  ⏱️ Tempo: 168.82s
  🧠 Memória: 2,446 MB (pico: 3,614 MB)
  📊 Performance: 30 linhas/s

📊 RECOMENDAÇÕES:
⚡ Mais rápido: chunk_size = 500 (30 linhas/s)
🧠 Menor uso de memória: chunk_size = 100 (1.1 GB)
⚖️ Mais eficiente: chunk_size = 500 (eficiência: 8.3)
```

### Recomendações por Tamanho de Arquivo

| Tamanho do Arquivo | chunk_size Recomendado | Justificativa |
|-------------------|------------------------|---------------|
| **> 15GB** | **100** | Máxima estabilidade, evita OOM |
| **10-15GB** | **500** | Balance ótimo performance/memória |
| **5-10GB** | **1000** | Performance boa, monitorar memória |
| **1-5GB** | **5000** | Performance máxima |
| **< 1GB** | **50000+** | Sem restrições de memória |

### ⚠️ Importante

- **Sempre execute os testes** antes de processar arquivos grandes em produção
- **Monitore o uso de memória** durante execuções longas
- **Tenha pelo menos 3x o tamanho do arquivo** em espaço livre em disco
- **Para arquivos >10GB**, considere usar drive externo para resultados

### Configuração Adaptativa Automática

O script `DAMICORE_Pareto_script_chunks_external.py` possui configuração adaptativa que ajusta automaticamente os parâmetros baseado no tamanho do arquivo:

```python
# Configuração automática baseada no tamanho
if file_size_gb >= 10:
    chunk_size = 100     # Ultra-conservador para arquivos grandes
    bootstrap_samples = 1
    max_columns_per_batch = 5
elif file_size_gb >= 5:
    chunk_size = 500     # Balance para arquivos médios
    bootstrap_samples = 2
    max_columns_per_batch = 10
else:
    chunk_size = 5_000   # Performance para arquivos pequenos
    bootstrap_samples = 3
    max_columns_per_batch = 20
```

## Gerenciamento de Dados com DVC

O projeto utiliza o [DVC (Data Version Control)](https://dvc.org/) para versionar e compartilhar grandes volumes de dados de análise. Isso garante reprodutibilidade e facilita o trabalho colaborativo sem sobrecarregar o Git.

### Pastas controladas pelo DVC
Atualmente, os seguintes diretórios estão sob controle do DVC:
- `data_projects/aggrada-pppp-sjrp-2025-05-15-block-yearly`
- `data_projects/aggrada-pppp-sjrp-2025-05-15-census_region-yearly`
- `data_projects/aggrada-pppp-sjrp-2025-05-15-neighborhood-yearly`

Essas pastas podem conter arquivos grandes de entrada, resultados intermediários ou finais de análises.

### Como baixar os dados após o clone
Após clonar o repositório, rode:
```bash
dvc pull
```
Isso irá baixar todos os dados versionados necessários para execução e reprodução dos experimentos.

### Como adicionar/remover dados do DVC
- Para adicionar um novo diretório ou arquivo grande ao DVC:
  ```bash
  dvc add caminho/do/dado
  git add caminho/do/dado.dvc caminho/do/.gitignore
  git commit -m "adiciona dado ao DVC"
  git push && dvc push
  ```
- Para remover um dado do DVC:
  ```bash
  dvc remove caminho/do/dado.dvc
  git add .
  git commit -m "remove dado do DVC"
  git push && dvc push
  ```

### Boas práticas
- **Nunca** faça commit direto de arquivos grandes no Git. Sempre use o DVC para dados volumosos.
- Sempre rode `dvc push` após adicionar novos dados para garantir que o storage remoto seja atualizado.
- Para baixar dados em outra máquina/ambiente, use sempre `dvc pull` após o clone.

Para dúvidas e detalhes, consulte a [documentação oficial do DVC](https://dvc.org/doc) ou entre em contato com os mantenedores do projeto.

DAMICORE/
├── src/
│   ├── __init__.py
│   ├── damicore.py
│   ├── ncd.py
│   ├── progress_bar.py
│   ├── tree.py
│   ├── tree_simplification.py
│   ├── scripts/
│   │   ├── DAMICORE_Filograma_script.py
│   │   ├── DAMICORE_Pareto_script.py
│   │   ├── DAMICORE_Pareto_script_chunks.py
│   │   ├── DAMICORE_Pareto_script_chunks_external.py
│   │   ├── DAMICORE_Pareto_script_chunks_per_chunk.py
│   │   └── pareto_frontier_local.py
│   └── utilities/
│       ├── generate_visualizations_from_newick.py
│       ├── test_chunk_sizes.py
│       ├── test_damicore_performance.py
│       └── test_resume_functionality.py
├── tests/
│   ├── test_damicore_pareto.py
│   ├── DAMICORE_Pareto_test.py
│   ├── test_tree_visualization.py
│   └── test_data/
│       └── ... (dados de teste)
├── data/
│   ├── sample_dengue/
│   └── sample_dengue.csv
├── config/
│   └── config.ini
├── docs/
│   ├── README.md
│   ├── KNOWN_WARNINGS.md
│   └── copilot-instructions.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── run.sh
└── .gitignore
```

### Descrição das Pastas Principais
- `src/`: Código-fonte principal do DAMICORE
- `src/scripts/`: Scripts executáveis e utilitários
- `tests/`: Testes automatizados e dados de teste
- `data/`: Dados de entrada e exemplos
- `config/`: Arquivos de configuração
- `docs/`: Documentação



## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/CristianoXico/DAMICORE
cd DAMICORE
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Como Executar

Veja o passo a passo completo de execução na seção "Passo a Passo Completo de Utilização" abaixo. Lá você encontra instruções para rodar localmente ou via Docker, além de dicas para uso de exemplos e testes.

## Formato dos Dados de Entrada

### Para Análise DAMICORE

O arquivo de entrada deve ser um CSV com as seguintes características:
- Codificação UTF-8
- Primeira linha contendo os nomes das colunas
- Valores podem ser numéricos ou textuais
- Sem restrições quanto ao número de colunas

Exemplo:
```csv
variavel_1,variavel_2,variavel_3
valor1,10,texto1
valor2,20,texto2
valor3,30,texto3
```

### Para Análise de Pareto

Se você planeja executar a análise de Fronteira de Pareto, o CSV deve incluir:
- Uma coluna chamada `join_CENSITARIO` (identificador único)
- Colunas com valores numéricos para otimização

Exemplo:
```csv
join_CENSITARIO,populacao,renda,idade_media
001,1000,2500,35
002,1500,3000,40
003,800,2000,30
```

## Dependências

As dependências principais estão listadas em `requirements.txt`. Consulte o item 7 do "Passo a Passo Completo de Utilização" para mais detalhes.
## Contribuindo

1. Faça um fork do projeto

## Exemplos

Na pasta `examples/` você encontrará arquivos de exemplo que podem ser usados para testar a funcionalidade do pipeline:

### example_input.csv

Um arquivo CSV simples que demonstra o formato básico de entrada esperado para a análise DAMICORE:

```csv
Variable,Value1,Value2,Value3
A,10,15,20
B,8,12,16
C,5,7,9
D,15,18,21
E,12,14,17
```

Para testar o pipeline com exemplos, siga as instruções detalhadas na seção "Passo a Passo Completo de Utilização". Os exemplos estão na pasta `examples/`.

## Passo a Passo Completo de Utilização

### 1. Instalação

Clone o repositório:
```bash
git clone https://github.com/CristianoXico/DAMICORE.git
cd DAMICORE
```

**Recomendação de boas práticas:**
Utilize um ambiente virtual Python para evitar conflitos de dependências com outros projetos. Exemplo:

```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
```

Instale as dependências:
```bash
pip install -r requirements.txt
```

### 2. Configuração Automatizada

Para configurar automaticamente o ambiente, execute:

```bash
python setup_config.py
```

Este script irá:
1. Detectar o caminho correto do DAMICORE CLI
2. Criar/atualizar o arquivo config.ini (em config/)
3. Criar diretórios necessários se não existirem

### 3. Executando o pipeline principal

#### Scripts Disponíveis

**1. Script Original (Arquivos Pequenos/Médios)**
```bash
python src/scripts/DAMICORE_Pareto_script.py
```
- Ideal para arquivos até 1GB
- Processamento tradicional em memória
- Mais rápido para datasets pequenos

**2. Script Chunked (Arquivos Grandes)**
```bash
python src/scripts/DAMICORE_Pareto_script_chunks.py
```
- Otimizado para arquivos 1-10GB
- Processamento em chunks para economizar memória
- Sistema de checkpoint/retomada automática

**3. Script Chunked External (Arquivos Ultra-Grandes)**
```bash
python src/scripts/DAMICORE_Pareto_script_chunks_external.py
```
- Otimizado para arquivos >10GB
- Salva resultados em drive externo
- Configuração adaptativa baseada no tamanho do arquivo

**4. Script Chunk-per-Chunk (Visualização Incremental)**
```bash
python src/scripts/DAMICORE_Pareto_script_chunks_per_chunk.py
```
- **NOVO**: Processamento chunk a chunk com visualizações incrementais
- Sistema de checkpoint/retomada automática robusto
- Visualizações adaptativas baseadas no número de colunas
- Bootstrap sampling adaptativo por chunk
- Barra de progresso em tempo real
- Visualização compilada final de todos os chunks
- Ideal para análise de progresso em tempo real

**Com Docker:**
```bash
docker build -t damicore .
docker run -it --rm -v $(pwd)/data:/app/data damicore
```

#### Scripts Utilitários

**1. Teste de Performance e Chunk Size**
```bash
# Testa diferentes tamanhos de chunk para otimizar performance
python src/utilities/test_chunk_sizes.py /caminho/para/arquivo.csv

# Testa performance completa do pipeline DAMICORE
python src/utilities/test_damicore_performance.py /caminho/para/arquivo.csv
```

**2. Geração de Visualizações a partir de Arquivos Newick**
```bash
# Gera visualizações a partir de arquivos newick existentes
python src/utilities/generate_visualizations_from_newick.py /caminho/para/diretorio/newick
```

**3. Teste do Sistema de Retomada**
```bash
# Testa funcionalidades de checkpoint/retomada automática
python src/utilities/test_resume_functionality.py
```

#### Recursos Avançados

**Sistema de Checkpoint/Retomada (✅ MELHORADO - Jan 2025):**
- ✅ **Correções Críticas**: Detecção de fatias falhadas, validação de integridade, verificação robusta de conclusão
- ✅ **Validação Automática**: Sistema verifica se arquivos newick existem e não estão corrompidos
- ✅ **Auto-Correção**: Fatias com arquivos perdidos/corrompidos são automaticamente reprocessadas
- Scripts `chunks`, `chunks_external`, `chunks_per_chunk` e `File_Slicer_Processor` possuem sistema robusto
- Em caso de falha/interrupção, o processamento continua do ponto onde parou
- Para reprocessar do zero, delete o arquivo `*_progress.json` correspondente
- **Novo**: Validação contínua de integridade dos arquivos gerados

**Visualizações Adaptativas:**
- Tamanho das imagens se adapta automaticamente ao número de colunas do dataset
- Baseline otimizado para 35 colunas, escala suavemente para datasets maiores
- Garante legibilidade independente do tamanho do dataset

**Bootstrap Sampling Adaptativo:**
- Número de amostras bootstrap se adapta ao número de chunks
- Mais chunks = menos amostras por chunk (otimiza tempo)
- Menos chunks = mais amostras por chunk (melhora qualidade)

### 4. Exemplos

Na pasta `examples/` você encontrará arquivos de exemplo que podem ser usados para testar a funcionalidade do pipeline.

### 5. Testes

Para executar os testes unitários:
```bash
python -m unittest discover tests
```

### 6. Estrutura das Pastas

A estrutura detalhada do projeto está na seção "Estrutura do Projeto" no início deste README.
### 7. Dependências

As principais dependências estão em `requirements.txt`. Incluem: pandas, numpy, matplotlib, toytree, toyplot, biopython, seaborn, sklearn.

### 8. Contribuindo

Para contribuir com o projeto, siga sempre o fluxo de Pull Request (PR):

1. Faça um fork do projeto

### Para Colaboradores

- **Sempre utilize Pull Requests (PRs)**: nunca faça commits diretamente na `main`. Todas as contribuições devem passar por revisão via PR.
- **Commits claros**: use mensagens descritivas e padronizadas.
- **Branches**: crie uma branch para cada nova feature ou correção.
- **Pull Requests**: explique a motivação da mudança e siga o passo a passo da seção "Contribuindo".
- **Testes**: sempre rode os testes antes de enviar um PR.
- **Linters**: utilize ferramentas como `flake8` ou `black` para padronizar o código.

## Testes

Para rodar os testes unitários, consulte o item 5 do "Passo a Passo Completo de Utilização". Os dados de teste estão em `tests/test_data/`.
Os testes verificam:

- Funcionalidade da análise DAMICORE
- Funcionalidade da análise de Fronteira de Pareto
- Geração correta de visualizações
- Manipulação adequada de dados

## Configuração

O arquivo `config.ini` contém as configurações padrão do projeto:

```ini
[Paths]
DAMICORE_CLI_PATH = damicore_py3/damicore.py

[Scripts]
DAMICORE_PARETO_SCRIPT = scripts_modulares/DAMICORE_Pareto_script.py
PARETO_FRONTIER_SCRIPT = scripts_modulares/pareto_frontier_local.py

[Data]
INPUT_DIR = test_data_scripts_modulares
EXAMPLES_DIR = examples

[Output]
RESULTS_DIR = results
TEMP_DIR = temp
```

Você pode modificar este arquivo para ajustar os caminhos dos scripts e diretórios conforme necessário.

## Docker

### Requisitos

- Docker
- Docker Compose

### Execução com Docker

#### Pré-requisitos

Para executar o DAMICORE usando Docker, você precisa ter:

* Docker instalado
* Docker Compose instalado
* Acesso root ou pertencer ao grupo docker

#### Instalação do Docker

No Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install docker.io
```

No Fedora:

```bash
sudo dnf install docker
```

No Arch Linux:

```bash
sudo pacman -S docker
```

#### Instalação do Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Configuração do Docker

1. Inicie o serviço:

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

2. Adicione seu usuário ao grupo docker (opcional):

```bash
sudo usermod -aG docker $USER
# Faça logout e login para aplicar as mudanças
```

#### Preparação do Ambiente

1. Clone o repositório e entre no diretório:

```bash
git clone [URL_DO_REPOSITÓRIO]
cd DAMICORE
```

2. Crie os diretórios necessários:

```bash
mkdir -p input results
```

### Executando o DAMICORE

Existem duas formas de executar o DAMICORE com Docker:

#### 1. Método Automático (Recomendado)

Execute o script automatizado:

```bash
./run.sh
```

O script irá:
* Criar os diretórios necessários
* Copiar o arquivo de exemplo se necessário
* Construir e executar o container

#### 2. Método Manual

1. Construa a imagem:

```bash
docker-compose build
```

2. Execute o container:

```bash
docker-compose up
```

### Uso do DAMICORE no Container

1. Coloque seus arquivos CSV no diretório `input/`

2. Quando o programa solicitar o caminho do arquivo, use:

```plaintext
/app/input/seu_arquivo.csv
```

3. Para análise de Pareto:
   * Digite 's' quando perguntado
   * Insira as variáveis separadas por vírgula

### Estrutura de Arquivos no Docker

```plaintext
DAMICORE/
├── input/                     # Coloque seus arquivos CSV aqui
├── results/                   # Os resultados serão salvos aqui
│   └── seu_arquivo/
│       ├── damicore_analysis/
│       │   ├── cloud_tree.pdf
│       │   ├── consensus_tree.pdf
│       │   └── tree_biopython.png
│       └── pareto_analysis/
│           └── pareto_filtered_*.csv
└── examples/                  # Arquivos de exemplo
```

### Solução de Problemas Comuns

#### Permissões

Se encontrar problemas de acesso aos arquivos:

```bash
sudo chown -R $USER:$USER input results
```

#### Limpeza do Docker

Para remover containers e volumes não utilizados:

```bash
docker-compose down -v
```

#### Logs e Debugging

Para ver logs detalhados:

```bash
docker-compose logs
```

#### Reconstrução

Para reconstruir após alterações no código:

```bash
docker-compose build --no-cache
```

### Exemplos Práticos

#### Exemplo 1: Análise DAMICORE Básica

```bash
# Copiar arquivo de exemplo
cp examples/example_input.csv input/

# Executar análise
./run.sh

# Quando solicitado, fornecer:
# Caminho: /app/input/example_input.csv
# Pareto: n
```

#### Exemplo 2: DAMICORE + Análise de Pareto

```bash
./run.sh

# Quando solicitado, fornecer:
# Caminho: /app/input/example_input.csv
# Pareto: s
# Variáveis: populacao,renda,idade_media
```

### Customização do Container

#### Recursos Computacionais

Para ajustar memória e CPU, edite `docker-compose.yml`:

```yaml
services:
  damicore:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
```

#### Volumes e Persistência

* `input/`: Diretório para arquivos de entrada
* `results/`: Diretório para resultados
* Os dados persistem entre execuções do container
