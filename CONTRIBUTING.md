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

- Python 3.12+ (obrigatório)
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

3. **Ative o ambiente virtual do projeto**
   ```bash
   # Ative damicore_env (Python 3.12 — ambiente padrão)
   source damicore_env/bin/activate
   
   # No Windows:
   # damicore_env\Scripts\activate
   
   # Verifique a versão
   python --version  # Deve ser 3.12+
   which python      # Deve conter "damicore_env"
   ```

4. **Instale as dependências de desenvolvimento**
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

5. **Configure o pre-commit**
   ```bash
   pre-commit install
   ```

### ⚠️ Ambientes Virtuais — Informações Importantes

**✅ Use APENAS `damicore_env`** para todo o desenvolvimento:

- ✅ **Ambiente obrigatório:** `damicore_env/` (Python 3.12)
- ❌ **NÃO use:** venv genérico, .venv, ou outros ambientes
- 🗑️ **Ambientes duplicados foram removidos** (venv, notebooks/.venv)

```bash
# Verificar ambiente correto
python --version       # Deve exibir 3.12.x
which python           # Deve conter "damicore_env"
pip list | grep numpy  # Verificar dependências instaladas
```

Se tiver problemas, recrie o ambiente:
```bash
rm -rf damicore_env
python3.12 -m venv damicore_env
source damicore_env/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 🏗️ Estrutura do Projeto

```
DAMICORE/
├── config/                      # Arquivos de configuração
├── docs/                        # Documentação adicional
├── examples/                    # Exemplos de uso
├── src/                         # Código-fonte principal
│   ├── __init__.py
│   ├── damicore.py             # Script principal de clustering
│   ├── ncd.py                  # Cálculo de distância NCD
│   ├── tree.py                 # Manipulação de árvores
│   ├── tree_simplification.py  # Simplificação de grafos
│   ├── progress_bar.py         # Utilidades
│   └── scripts/                # Scripts de análise
│       ├── checkpoint_manager.py
│       ├── DAMICORE_Filograma_script.py
│       ├── DAMICORE_File_Slicer_Processor.py
│       └── ...
├── notebooks/                  # Notebooks e dados de teste
├── damicore_env/              # Ambiente virtual (Python 3.12)
├── .gitignore
├── .pre-commit-config.yaml    # Configuração pre-commit
├── Dockerfile                  # Imagem Docker
├── DOCKER.md                   # Guia Docker consolidado
├── README.md                   # Documentação principal
├── CONTRIBUTING.md             # Este arquivo
├── WORKFLOW_PR.md              # Workflow de Pull Requests
└── requirements.txt            # Dependências Python
```

## 🔄 Fluxo de Trabalho com Branches

### Branches do Projeto

- **`main`:** Código consolidado e pronto para produção
- **`sandbox`:** Experimentações e testes — use para PR de features

### Criando uma Feature/Fix

1. **Sincronize a branch base**
   ```bash
   git checkout sandbox
   git pull origin sandbox
   ```

2. **Crie uma branch de feature**
   ```bash
   # Nomes recomendados:
   git checkout -b feature/minha-nova-funcionalidade
   # ou
   git checkout -b fix/corrigir-esse-bug
   # ou
   git checkout -b docs/melhorar-documentacao
   ```

3. **Faça suas alterações**
   - Modifique código, testes, documentação conforme necessário
   - Siga os padrões de código (veja seção abaixo)
   - Adicione testes para novas funcionalidades

4. **Verifique seu código**
   ```bash
   # Execute testes
   pytest tests/
   
   # Formatação com black
   black src/ tests/
   
   # Verificação estática
   flake8 src/ tests/
   
   # Type checking (opcional)
   mypy src/ --ignore-missing-imports
   ```

5. **Faça commit das alterações**
   ```bash
   git add src/ tests/
   git commit -m "feat: descrição clara da mudança"
   ```

6. **Envie para o remoto**
   ```bash
   git push origin feature/minha-nova-funcionalidade
   ```

7. **Abra um Pull Request**
   - Vá para [GitHub DAMICORE](https://github.com/CristianoXico/DAMICORE)
   - Clique em "New Pull Request"
   - **Base:** `sandbox` (não main!)
   - **Compare:** sua branch `feature/...`
   - Preencha o template de PR com:
     - Descrição clara do que foi mudado
     - Por quê essa mudança é necessária
     - Como testar
     - Screenshots/exemplos se apropriado
   - Submeta

### Revisar e Mergear

- Seu PR será revisado
- Faça ajustes conforme sugerido
- Após aprovação, será merged automaticamente

## 📝 Padrões de Código

### Convenções de Commit

Utilizamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<escopo>): <assunto>

<corpo>

<rodapé>
```

**Tipos:**
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudanças na documentação
- `style:` Formatação, sem mudança funcional
- `refactor:` Refatoração de código
- `perf:` Melhoria de desempenho
- `test:` Adicionando/atualizando testes
- `chore:` Tarefas, dependências, etc.

**Exemplos:**
```
feat(clustering): adiciona algoritmo HDBSCAN

Implementa novo algoritmo de clustering HDBSCAN como alternativa ao
fastgreedy. Inclui testes de desempenho e comparação com métodos
anteriores.

Fixes #42
```

```
fix(ncd): corrige cálculo de distância com pesos negativos

Garante que todos os pesos sejam positivos após normalização,
evitando erros no algoritmo community_fastgreedy.

Fixes #38
```

### Formatação de Código

```bash
# Formatação automática com black
black src/

# Verificação de estilo com flake8
flake8 src/ --max-line-length=88

# Sorted imports
isort src/
```

**Regras:**
- Tamanho máximo de linha: **88 caracteres**
- Aspas: **duplas** (`"string"`) por padrão
- Indentação: **4 espaços**
- Sem imports não utilizados

### Docstrings

Use formato Google Style:

```python
def funcao_exemplo(parametro1: str, parametro2: int) -> bool:
    """Descrição breve em uma linha.
    
    Descrição mais detalhada se necessário. Explique o comportamento
    da função, seus usos e qualquer informação importante.
    
    Args:
        parametro1: Descrição do primeiro parâmetro.
        parametro2: Descrição do segundo parâmetro.
    
    Returns:
        Descrição do valor retornado.
    
    Raises:
        ValueError: Quando parametro1 é vazio.
        TypeError: Quando parametro2 não é inteiro.
    
    Example:
        >>> resultado = funcao_exemplo("teste", 42)
        >>> print(resultado)
        True
    """
    if not parametro1:
        raise ValueError("parametro1 não pode ser vazio")
    
    if not isinstance(parametro2, int):
        raise TypeError("parametro2 deve ser inteiro")
    
    return True
```

## 🧪 Testes

### Executando Testes

```bash
# Todos os testes
pytest

# Com verbose
pytest -v

# Cobertura de código
pytest --cov=src tests/

# Testes específicos
pytest tests/test_ncd.py::test_distance_matrix
```

### Escrevendo Testes

Coloque testes em `tests/`:

```python
import pytest
from src.ncd import distance_matrix

class TestDistanceMatrix:
    """Testes para cálculo de matriz de distância NCD."""
    
    def test_distance_matrix_basic(self):
        """Testa cálculo básico de matriz de distância."""
        # Setup
        data = {"file1": b"data1", "file2": b"data2"}
        
        # Execute
        result = distance_matrix(data)
        
        # Assert
        assert result.shape == (2, 2)
        assert result[0, 0] == 0  # Diagonal deve ser 0
        assert result[0, 1] == result[1, 0]  # Simétrica
    
    def test_distance_matrix_empty(self):
        """Testa comportamento com entrada vazia."""
        with pytest.raises(ValueError):
            distance_matrix({})
```

**Dicas:**
- Mantenha testes independentes
- Use fixtures para código compartilhado
- Nomeie testes de forma descritiva
- Aim para >80% cobertura

## 📤 Enviando Mudanças (PR)

### Checklist Antes de Submeter

- [ ] Código foi testado localmente
- [ ] Testes novos foram adicionados
- [ ] Documentação foi atualizada
- [ ] Commits seguem Conventional Commits
- [ ] Sem merge conflicts com `sandbox`
- [ ] Black, flake8 passam
- [ ] Cobertura de testes mantida/melhorada

### Atualizando PR Existente

Se precisar fazer ajustes após feedback:

```bash
# Faça ajustes no código
# ... edite arquivos ...

# Faça commit dos ajustes
git add .
git commit -m "refactor: ajusta conforme feedback"

# Force push para atualizar a PR
git push --force-with-lease origin feature/sua-branch
```

## 🐛 Relatando Problemas

Antes de abrir uma issue, verifique se já existe similitude.

**Template de Issue:**

```markdown
## Descrição do Problema
Descrição clara e concisa do que está acontecendo.

## Passos para Reproduzir
1. Passo 1
2. Passo 2
3. Passo 3...

## Comportamento Esperado
O que deveria acontecer.

## Comportamento Atual
O que realmente está acontecendo.

## Ambiente
- Python: 3.12.x
- Sistema: Linux/macOS/Windows
- Versão DAMICORE: (branch ou commit)
- Dependências relevantes: (output de pip freeze)

## Logs/Traceback
```
Colar erro aqui
```

## Capturas de Tela
(se aplicável)
```

## 💡 Solicitando Recursos

**Template de Feature Request:**

```markdown
## Descrição
Descrição clara do recurso solicitado.

## Motivação
Por quê esse recurso seria útil? Quais problemas resolveria?

## Casos de Uso
Exemplos específicos de como seria usado.

## Alternativas Consideradas
Outras formas de resolver o mesmo problema?

## Contexto Adicional
Qualquer outra informação relevante.
```

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a [Licença MIT](LICENSE).

---

## 📞 Dúvidas?

- 📖 Leia [WORKFLOW_PR.md](WORKFLOW_PR.md) para detalhes do workflow
- 🐳 Leia [DOCKER.md](DOCKER.md) para deploy com Docker
- 📚 Leia [README.md](README.md) para documentação geral

Obrigado por ajudar a melhorar o DAMICORE! Seu tempo e esforço são muito apreciados. 🚀

**Última Atualização:** 12 de novembro de 2025
