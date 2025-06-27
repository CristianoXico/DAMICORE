# DAMICORE - Pipeline de Análise Multi-Critério

Pipeline para análise de dados utilizando FS OPA (Feature Selection - Orientação a Partição de Árvore) e Fronteira de Pareto para otimização multiobjetivo. Projetado para lidar com conjuntos de dados de diferentes tamanhos, garantindo uma análise abrangente e detalhada.

## 🚀 Funcionalidades

- **Leitura e Pré-processamento de Dados**
  - Suporte a arquivos CSV com detecção automática de colunas compostas
  - Normalização de nomes de colunas
  - Tratamento de dados ausentes
  - Compatível com conjuntos de dados de vários tamanhos

- **Análise de Consenso (NCD)**
  - Cálculo de matriz de distância NCD (Normalized Compression Distance)
  - Geração de árvore de consenso em formato ASCII
  - Identificação automática de clusters

- **Seleção de Critérios (FS-OPA)**
  - Seleção interativa do número de critérios (2, 4 ou 8)
  - Análise de dispersão entre grupos
  - Geração de árvores de decisão BEST/WORST em ASCII
  - Exportação de resultados detalhados

- **Análise de Pareto**
  - Seleção interativa de variáveis para análise
  - Identificação da fronteira de Pareto
  - Cálculo de métricas de qualidade
  - Exportação de resultados em CSV

## 🔍 Visualização da Árvore de Consenso

A visualização da árvore de consenso é gerada automaticamente com base nas colunas presentes no conjunto de dados. A árvore inclui:

- **Rótulos claros** para todas as colunas
- **Valores de suporte** nos nós internos (quando disponíveis)
- **Destaque visual** para valores de suporte baixos (abaixo de 70%)
- **Legenda** explicando as cores e símbolos utilizados

### Formato da Saída

A árvore de consenso é gerada em dois formatos:
1. **Visual (SVG/PNG)**: Para fácil visualização das relações entre as colunas
2. **Texto (Newick)**: Para análise posterior em outras ferramentas

### Exemplo de Uso

```bash
# Gerar apenas a visualização da árvore de consenso
python pipeline_novo.py --input dados/entrada.csv --modo consenso

# Gerar visualização com opções avançadas
python pipeline_novo.py --input dados/entrada.csv --modo consenso --largura 1600 --altura 1000 --formato svg
```

## 📦 Instalação

### Pré-requisitos
- Python 3.7 ou superior
- pip (gerenciador de pacotes do Python)
- Git (opcional, apenas para clonar o repositório)

### Configuração do Ambiente Virtual

1. **Clone o repositório** (ou baixe os arquivos):
   ```bash
   git clone https://github.com/seu-usuario/damicore.git
   cd damicore
   ```

2. **Crie um ambiente virtual** (recomendado para isolar as dependências):
   ```bash
   # No Windows:
   python -m venv venv
   
   # No Linux/Mac:
   python3 -m venv venv
   ```

3. **Ative o ambiente virtual**:
   ```bash
   # No Windows (PowerShell):
   .\venv\Scripts\activate
   
   # No Windows (Command Prompt):
   venv\Scripts\activate.bat
   
   # No Linux/Mac:
   source venv/bin/activate
   ```
   
   Você saberá que o ambiente virtual está ativado quando vir `(venv)` no início do prompt de comando.

4. **Atualize o pip** (opcional, mas recomendado):
   ```bash
   python -m pip install --upgrade pip
   ```

5. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Se o arquivo `requirements.txt` não existir, instale as dependências manualmente:
   ```bash
   pip install numpy pandas scipy scikit-learn matplotlib seaborn toytree biopython
   ```

### Verificação da instalação

Para verificar se tudo foi instalado corretamente, execute:

```bash
python -c "import numpy, pandas, toytree; print('Todas as dependências foram instaladas com sucesso!')"
```

### Desativando o ambiente virtual

Quando terminar de usar o DAMICORE, você pode desativar o ambiente virtual com:

```bash
deactivate
```

### Dicas úteis

- **Reativar o ambiente virtual**: Sempre que você reabrir o terminal, precisará reativar o ambiente virtual com o comando de ativação apropriado para seu sistema operacional.

- **Instalação de dependências adicionais**: Se precisar instalar pacotes adicionais, certifique-se de que o ambiente virtual esteja ativado antes de usar `pip install`.

- **Compatibilidade**: Este projeto requer Python 3.7 ou superior. Verifique sua versão do Python com `python --version`.

- **Problemas com permissões no Windows**: Se encontrar erros de permissão ao ativar o ambiente virtual, execute o PowerShell como administrador e tente novamente.

## 🚀 Como Usar

### Execução Básica

```bash
python pipeline_novo.py --input dados/entrada.csv
```

### Opções de Linha de Comando

- `--input`: Caminho para o arquivo CSV de entrada (obrigatório)
- `--output`: Diretório de saída (padrão: 'resultados')
- `--sep`: Separador do CSV (padrão: ',')
- `--encoding`: Codificação do arquivo (padrão: 'utf-8')
- `--no-prompt`: Execução sem interação do usuário (usa valores padrão)

### Fluxo de Execução

1. **Leitura dos Dados**
   - Carrega o arquivo CSV especificado
   - Detecta e processa colunas compostas
   - Exibe um resumo dos dados

2. **Análise de Consenso**
   - Calcula a matriz de distância NCD
   - Gera e exibe a árvore de consenso em ASCII
   - Identifica clusters automaticamente

3. **Seleção de Critérios (FS-OPA)**
   - Solicita o número de critérios (2, 4 ou 8)
   - Seleciona as variáveis mais discriminantes
   - Gera e exibe as árvores de decisão BEST/WORST
   - Exporta os resultados para o diretório de saída

4. **Análise de Pareto**
   - Permite selecionar variáveis para análise
   - Identifica a fronteira de Pareto
   - Calcula métricas de qualidade
   - Exporta os resultados para CSV

## 📂 Estrutura do Projeto

```
damicore/
├── pipeline_novo.py      # Script principal do pipeline
├── fs_opa.py            # Implementação do FS-OPA
├── pareto_analysis.py   # Análise de Pareto
├── requirements.txt     # Dependências do projeto
└── README.md           # Esta documentação
```

## 📊 Saídas

O pipeline gera os seguintes arquivos de saída:

- `resultados/consenso/`
  - `matriz_ncd.csv`: Matriz de distância NCD
  - `arvore_consenso.txt`: Árvore de consenso em formato de texto
  - `arvore_consenso.svg`: Visualização vetorial da árvore (SVG)
  - `arvore_consenso.png`: Imagem da árvore (PNG)
  - `estatisticas_suporte.json`: Estatísticas detalhadas sobre os valores de suporte dos nós

- `resultados/fs_opa/`
  - `variaveis_selecionadas.json`: Variáveis selecionadas pelo FS-OPA
  - `arvore_best.txt`: Árvore de decisão para o melhor caso
  - `arvore_worst.txt`: Árvore de decisão para o pior caso

- `resultados/pareto/`
  - `pareto_[VARIAVEIS]_[TIMESTAMP].csv`: Resultados da análise de Pareto

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e enviar pull requests.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🔍 Solução de Problemas Comuns

### Valores de Suporte Iguais

Se todos os nós internos estiverem mostrando o mesmo valor de suporte (geralmente 1.0 ou 100%), isso pode indicar que:

1. Todas as árvores de entrada têm a mesma topologia
2. Os valores de suporte não foram corretamente extraídos
3. O método de consenso não está preservando os valores de suporte

### Colunas Ausentes na Visualização

Se alguma coluna não estiver aparecendo na visualização:

1. Verifique se o arquivo de entrada contém as colunas esperadas
2. Confirme se os nomes das colunas estão corretos
3. Verifique se há valores ausentes que possam estar afetando a análise
4. Considere reduzir o número de colunas se o conjunto de dados for muito grande

## 📚 Referências

- Metodologia FS OPA
- Análise de Fronteira de Pareto
- Normalized Compression Distance (NCD)
- Documentação do toytree: https://toytree.readthedocs.io/
- Biopython: https://biopython.org/
