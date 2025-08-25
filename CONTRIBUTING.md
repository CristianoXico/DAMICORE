# Guia de Contribuição para o DAMICORE

Obrigado por considerar contribuir para o projeto DAMICORE! Este guia irá ajudá-lo a configurar o ambiente de desenvolvimento, entender a estrutura do projeto e enviar suas contribuições.

## 📋 Índice

1. [Código de Conduta](#código-de-conduta)
2. [Configuração do Ambiente](#-configuração-do-ambiente)
3. [Estrutura do Projeto](#-estrutura-do-projeto)
4. [Fluxo de Trabalho](#-fluxo-de-trabalho)
5. [Padrões de Código](#-padrões-de-código)
6. [Testes](#-testes)
7. [Enviando Mudanças](#-enviando-mudanças)
8. [Relatando Problemas](#-relatando-problemas)
9. [Solicitando Recursos](#-solicitando-recursos)

## Código de Conduta

Este projeto adere ao [Código de Conduta de Código Aberto](https://www.contributor-covenant.org/pt-br/version/2/1/code_of_conduct/).

## 🛠️ Configuração do Ambiente

### Pré-requisitos

- Python 3.8+
- Git
- Docker (opcional, mas recomendado para consistência)
- pip (gerenciador de pacotes Python)

### Configuração Inicial

1. **Fork o repositório**
   - Clique em "Fork" no canto superior direito da [página do repositório](https://github.com/CristianoXico/DAMICORE)

2. **Clone o repositório**
   ```bash
   git clone https://github.com/SEU-USUARIO/DAMICORE.git
   cd DAMICORE
   ```

3. **Configure o ambiente virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

4. **Instale as dependências**
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

5. **Configure o pre-commit**
   ```bash
   pre-commit install
   ```

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
├── README.md                # Documentação principal
├── CONTRIBUTING.md          # Este arquivo
└── requirements.txt         # Dependências Python
```

## 🔄 Fluxo de Trabalho

1. **Crie uma branch**
   ```bash
   git checkout -b feature/nome-da-feature
   # ou
   git checkout -b fix/corrigir-bug
   ```

2. **Faça suas alterações**
   - Siga os padrões de código
   - Adicione testes quando necessário
   - Atualize a documentação

3. **Verifique seu código**
   ```bash
   # Execute os testes
   pytest
   
   # Verifique a formatação
   black .
   
   # Verifique erros estáticos
   flake8
   ```

4. **Faça commit das alterações**
   ```bash
   git add .
   git commit -m "feat: adiciona nova funcionalidade"
   ```

5. **Envie as alterações**
   ```bash
   git push origin feature/nome-da-feature
   ```

6. **Abra um Pull Request**
   - Vá para o repositório original
   - Clique em "New Pull Request"
   - Siga o template de PR

## 📝 Padrões de Código

### Convenções de Commit

Utilizamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudanças na documentação
- `style:` Formatação, ponto e vírgula, etc. (sem mudança de código)
- `refactor:` Mudança que não corrige um bug nem adiciona uma funcionalidade
- `perf:` Mudança de código que melhora o desempenho
- `test:` Adicionando testes ausentes
- `chore:` Atualização de tarefas, configuração do gerenciador de pacotes, etc.

Exemplo:
```
feat: adiciona suporte a arquivos CSV grandes

Adiciona processamento em lotes para arquivos maiores que 1GB.
Inclui testes de desempenho e tratamento de erros.

Fixes #123
```

### Formatação

- Use `black` para formatação automática
- Tamanho máximo de linha: 88 caracteres
- Use aspas duplas (`"`) para strings

### Documentação

- Documente todas as funções públicas com docstrings no formato Google Style
- Mantenha o README.md atualizado
- Adicione exemplos de uso quando apropriado

## 🧪 Testes

### Executando Testes

```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/test_meu_modulo.py

# Com cobertura de código
pytest --cov=src tests/
```

### Escrevendo Testes

- Testes devem ser colocados no diretório `tests/`
- Nomeie os arquivos de teste como `test_*.py`
- Use fixtures do pytest para código compartilhado
- Mantenha os testes independentes e rápidos

## 📤 Enviando Mudanças

1. Atualize sua branch com a branch principal
   ```bash
   git fetch origin main
   git rebase origin/main
   ```

2. Resolva quaisquer conflitos

3. Execute os testes novamente

4. Envie suas alterações
   ```bash
   git push --force-with-lease origin feature/nome-da-feature
   ```

5. Abra um Pull Request

## 🐛 Relatando Problemas

Antes de abrir uma issue:

1. Verifique se já existe uma issue semelhante
2. Use o template de issue fornecido
3. Inclua informações detalhadas:
   - Passos para reproduzir
   - Comportamento esperado vs. real
   - Capturas de tela, se aplicável
   - Versão do Python e dependências

## 💡 Solicitando Recursos

Para solicitar novos recursos:

1. Verifique se o recurso já foi solicitado
2. Explique por que o recurso seria útil
3. Inclua casos de uso específicos
4. Se possível, sugira uma implementação

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a [Licença MIT](LICENSE).

---

Obrigado por ajudar a melhorar o DAMICORE! Seu tempo e esforço são muito apreciados. 🚀
