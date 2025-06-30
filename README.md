# DAMICORE - Análise de Dados e Fronteira de Pareto

Este projeto implementa um pipeline de análise que combina o método DAMICORE (Data Mining of Code Repositories) com análise de Fronteira de Pareto para exploração e visualização de dados.

## Estrutura do Projeto

```
DAMICORE/
├── scripts_modulares/          # Scripts principais
│   ├── DAMICORE_Pareto_script.py  # Script integrado principal
│   └── pareto_frontier_local.py    # Módulo de análise Pareto
├── damicore_py3/              # Core da implementação DAMICORE
│   ├── damicore.py
│   ├── ncd.py
│   ├── progress_bar.py
│   ├── tree.py
│   └── tree_simplification.py
├── test_data_scripts_modulares/  # Dados de teste
└── requirements.txt           # Dependências do projeto
```

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITÓRIO]
cd DAMICORE
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Como Executar

### Script Principal (DAMICORE + Pareto)

O script `DAMICORE_Pareto_script.py` integra a análise DAMICORE com análise opcional de Fronteira de Pareto:

```bash
python scripts_modulares/DAMICORE_Pareto_script.py
```

O script irá:
1. Solicitar o caminho do arquivo CSV de entrada
2. Executar a análise DAMICORE
3. Gerar visualizações (Cloud Tree, Consensus Tree, Árvore Filogenética)
4. Opcionalmente executar a análise de Fronteira de Pareto

Os resultados serão salvos em uma pasta com o mesmo nome do arquivo de entrada, contendo:
- `damicore_analysis/`: Resultados da análise DAMICORE
- `pareto_analysis/`: Resultados da análise de Fronteira de Pareto (se executada)

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

## Dependências Principais

- pandas
- numpy
- matplotlib
- toytree
- toyplot
- biopython
- seaborn
- sklearn

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

Para testar o pipeline com este exemplo:

```bash
python scripts_modulares/DAMICORE_Pareto_script.py
# Quando solicitado, forneça o caminho: examples/example_input.csv
```

## Configuração Automatizada

Para configurar automaticamente o ambiente, execute:

```bash
python setup_config.py
```

Este script irá:

1. Detectar o caminho correto do DAMICORE CLI
2. Criar/atualizar o arquivo config.ini
3. Criar diretórios necessários se não existirem

## Testes

### Estrutura de Testes

- `tests/`: Testes unitários
- `test_data_scripts_modulares/`: Dados de teste para scripts modulares
  - `ncd_input/`: Dados para testes de NCD (Normalized Compression Distance)
  - `portugues/`: Exemplos em português
  - `referencia/`: Dados de referência

### Executando os Testes

Para executar os testes unitários:

```bash
python -m unittest discover tests
```

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
