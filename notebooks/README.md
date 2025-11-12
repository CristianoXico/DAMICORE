# INCT Combate à Fome - Documentação dos Notebooks

Este repositório contém uma coleção de notebooks Jupyter para análise de dados relacionados ao combate à fome no Brasil. Abaixo está a documentação de cada notebook e quando utilizá-lo.

## Lista de Notebooks

### 1. camadas_espaciais_br.ipynb

**Objetivo**: Criar um DataFrame pandas a partir de dados JSON fornecidos pela API do IBGE, contendo informações sobre municípios brasileiros.

**Quando usar**:

- Quando você precisa de uma base de dados estruturada com informações municipais do Brasil
- Para obter dados atualizados de localidades brasileiras diretamente da API do IBGE
- Para transformar dados aninhados em JSON em um formato tabular (CSV)

**Saída**: Um arquivo CSV contendo informações detalhadas sobre os municípios brasileiros.

---

### 2. check_inside_variable.ipynb

**Objetivo**: Analisar e processar variáveis em conjuntos de dados.

**Quando usar**:

- Para inspecionar a estrutura de variáveis em conjuntos de dados complexos
- Realizar análises exploratórias de dados com múltiplas variáveis

**Funcionalidades**:

- Análise de tipos de dados
- Processamento de valores ausentes
- Construção de estruturas de dados aninhadas (JavaScript Object Notation - JSON)

---

### 3. filtering_columns_dataset_br.ipynb

**Objetivo**: Filtrar e processar colunas de conjuntos de dados.

**Quando usar**:

- Para limpar e preparar conjuntos de dados
- Filtrar colunas relevantes para análise

**Características**:

- Processamento de dados por estado
- Consolidação de colunas
- Geração de relatórios resumidos

---

### 4. local_analysis.ipynb

**Objetivo**: Análise local de dados, configurado para funcionar em ambientes locais.

**Quando usar**:

- Para executar análises sem depender de ambientes em nuvem
- Quando se trabalha com dados sensíveis que não podem ser carregados em serviços online
- Para processar grandes volumes de dados localmente

**Configuração**:

- Requer instalação local do Python e das bibliotecas necessárias
- Pode ser adaptado para diferentes conjuntos de dados locais

---

### 5. csv_to_filograma.ipynb

**Objetivo**: Converter dados no formato csv para visualizações de filograma.

**Quando usar**:

- Para visualizar relações filogenéticas ou hierárquicas
- Quando se trabalha com dados biológicos ou de classificação
- Para criar representações visuais de árvores filogenéticas

---

### 6. pareto_frontier_analysis_3_1_no_nan.ipynb

**Objetivo**: Realizar análise de fronteira de Pareto em conjuntos de dados, otimizado para lidar com valores ausentes.

**Quando usar**:

- Para otimização multiobjetivo
- Identificar soluções ótimas de Pareto
- Análise de trade-offs entre diferentes variáveis

**Vantagens**:

- Tratamento robusto de valores ausentes
- Visualizações claras das fronteiras de Pareto
- Fácil integração com conjuntos de dados existentes

---

### 7. plot_categorias_database.ipynb

**Objetivo**: Criar visualizações para categorias em bancos de dados.

**Quando usar**:

- Para explorar a distribuição de categorias em conjuntos de dados
- Gerar gráficos e visualizações para análise exploratória
- Compreender a composição de variáveis categóricas

**Tipos de visualizações**:

- Gráficos de barras
- Gráficos de pizza
- Histogramas
- Outras visualizações categóricas

---

### 8. polygons_to_geojson_br.ipynb

**Objetivo**: Converter polígonos para o formato GeoJSON, com foco em dados brasileiros.

**Quando usar**:

- Para trabalhar com dados geoespaciais do Brasil
- Converter formatos de polígonos para GeoJSON
- Preparar dados para visualização em mapas interativos

**Aplicações**:

- Mapas temáticos
- Análise espacial
- Visualização de dados geográficos

## Como usar

### Configuração do Ambiente Virtual

Recomendamos o uso de um ambiente virtual para isolar as dependências do projeto. Siga os passos abaixo:

1. Crie um ambiente virtual (se ainda não tiver um):

   ```bash
   # No Linux/MacOS
   python -m venv venv

   # No Windows
   python -m venv venv
   ```

2. Ative o ambiente virtual:

   ```bash
   # No Linux/MacOS
   source venv/bin/activate

   # No Windows (PowerShell)
   .\venv\Scripts\Activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. (Opcional) Se estiver usando Jupyter Notebook/Lab, instale o kernel do ambiente virtual:

   ```bash
   python -m ipykernel install --user --name=venv
   ```

### Executando os Notebooks

1. Com o ambiente virtual ativado, inicie o Jupyter:

   ```bash
   jupyter notebook
   ```

   Ou para JupyterLab:

   ```bash
   jupyter lab
   ```

2. Navegue até o notebook desejado e execute as células.

3. Após terminar, desative o ambiente virtual:

   ```bash
   deactivate
   ```

### Dados

Certifique-se de que os dados necessários estejam no diretório correto, conforme especificado em cada notebook. Alguns notebooks podem exigir o download de conjuntos de dados adicionais.

## Requisitos

- Python 3.7+
- Jupyter Notebook/Lab
- Bibliotecas listadas em `requirements.txt`

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Contato

Para mais informações, entre em contato com a equipe do INCT Combate à Fome.
