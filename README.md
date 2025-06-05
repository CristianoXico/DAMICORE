# DAMICORE - Pipeline de Análise Multi-Critério

Pipeline para análise de dados utilizando FS OPA (Feature Selection - Orientação a Partição de Árvore) e Fronteira de Pareto para otimização multiobjetivo.

## 🚀 Funcionalidades

- **Leitura e Pré-processamento de Dados**
  - Suporte a arquivos CSV com detecção automática de colunas compostas
  - Normalização de nomes de colunas
  - Tratamento de dados ausentes

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

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/damicore.git
   cd damicore
   ```

2. Crie e ative um ambiente virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

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

## 📚 Referências

- Metodologia FS OPA
- Análise de Fronteira de Pareto
- Normalized Compression Distance (NCD)
