# Workflow de Pull Requests (PRs) — DAMICORE

## 📋 Visão Geral

Este documento define o workflow padrão para desenvolvimento, testes e integração no repositório DAMICORE.

**Branches principais:**
- `main` — código consolidado e pronto para produção
- `sandbox` — experimentações, testes e desenvolvimento

---

## 🔄 Workflow Padrão

### 1. Criar uma Feature Branch (a partir de `sandbox`)

```bash
# Sincronizar sandbox com remoto
git checkout sandbox
git pull origin sandbox

# Criar branch de feature
git checkout -b feature/nome-da-funcionalidade

# Exemplo
git checkout -b feature/melhorar-clustering
```

**Convenção de nome:**
- `feature/descricao-curta` — novas funcionalidades
- `fix/descricao-do-bug` — correções de bugs
- `docs/descricao` — documentação
- `refactor/descricao` — refatorações
- `test/descricao` — testes

---

### 2. Desenvolver e Commitar

```bash
# Fazer alterações no código
nano src/arquivo.py

# Adicionar mudanças
git add src/arquivo.py

# Commitar com mensagem descritiva
git commit -m "Descrição clara do que foi feito

Detalhes opcionais:
- O que mudou
- Por que mudou
- Como testar (se aplicável)
"
```

**Convenção de commit:**
- Comece com verbo: "Adiciona", "Corrige", "Refatora", "Documenta"
- Primeira linha com até 50 caracteres
- Deixe linha em branco e adicione mais detalhes se necessário
- Exemplo: `Corrige clustering com pesos negativos em NCD`

---

### 3. Enviar para Remoto e Criar PR

```bash
# Enviar branch para remoto
git push origin feature/melhorar-clustering

# Abrir PR manualmente no GitHub (ou usar gh)
# URL: https://github.com/CristianoXico/DAMICORE/pull/new/feature/melhorar-clustering
```

**Se usar GitHub CLI (`gh`):**
```bash
# Criar PR interativamente
gh pr create --base sandbox --head feature/melhorar-clustering --title "Melhorar clustering" --body "Descrição da mudança"

# Ou via browser
gh pr create --web
```

---

### 4. Revisar e Testar PR

Após criar a PR:

1. **Executar testes localmente** (antes de criar a PR):
   ```bash
   pytest tests/
   python -m flake8 src/
   ```

2. **Verificar mudanças** no GitHub:
   - Clique em "Files changed"
   - Revise o diff
   - Deixe comentários se necessário

3. **CI/CD** (se configurado):
   - Automaticamente roda testes e verificações
   - Aguarde status verde ✅

---

### 5. Merge da PR

**Opção A — Merge direto (para small features/fixes):**
```bash
# No GitHub, clique em "Merge pull request" → "Confirm merge"
```

**Opção B — Merge via CLI:**
```bash
gh pr merge <PR_NUMBER> --merge --delete-branch
```

**Opção C — Merge local (se preferir mais controle):**
```bash
# Sincronizar sandbox
git checkout sandbox
git pull origin sandbox

# Integrar feature (via merge ou rebase)
git merge feature/melhorar-clustering
# ou
git rebase feature/melhorar-clustering

# Enviar para remoto
git push origin sandbox
```

---

## 🎯 Fluxo Completo com Exemplo

### Cenário: Corrigir bug no clustering

```bash
# 1. Ir para sandbox e sincronizar
git checkout sandbox
git pull origin sandbox

# 2. Criar branch de fix
git checkout -b fix/negative-weights-ncd

# 3. Fazer mudanças (abrir editor)
nano src/damicore.py
# ... editar código para corrigir o bug ...

# 4. Testar localmente
python -m pytest tests/test_clustering.py
python src/damicore.py --test-data

# 5. Commitar
git add src/damicore.py
git commit -m "Corrige pesos negativos no algoritmo NCD

- Adiciona validação de pesos após cálculo de distância
- Garante que todos os pesos são positivos para community_fastgreedy
- Adiciona teste unitário para verificar
"

# 6. Enviar para remoto
git push origin fix/negative-weights-ncd

# 7. Criar PR no GitHub (browser ou gh)
# Base: sandbox
# Compare: fix/negative-weights-ncd

# 8. Aguardar revisão, fazer ajustes se necessário
# (novos commits para a mesma branch automaticamente aparecem na PR)

# 9. Merge (após aprovação)
# No GitHub: Merge pull request

# 10. Limpar branch local (opcional)
git branch -d fix/negative-weights-ncd
```

---

## 🔗 Integração Sandbox → Main

Quando código em `sandbox` estiver consolidado e pronto para produção:

```bash
# 1. Sincronizar e mergear sandbox em main
git checkout main
git pull origin main

# 2. Mergear sandbox (considere usar --no-ff para histórico claro)
git merge --no-ff sandbox -m "Integra sandbox consolidado em main"

# 3. Enviar para remoto
git push origin main

# 4. Criar tag de versão (opcional mas recomendado)
git tag -a v1.2.0 -m "Release versão 1.2.0 - Novos algoritmos"
git push origin v1.2.0
```

---

## ✅ Checklist antes de Criar PR

- [ ] Código foi testado localmente
- [ ] Commit message é clara e descritiva
- [ ] Sem arquivos desnecessários committed (`.pyc`, `__pycache__`, etc.)
- [ ] Código segue style guide (flake8, black)
- [ ] Documentação foi atualizada (se aplicável)
- [ ] Sem merge conflicts com a base branch
- [ ] Descrição da PR explica o "porquê"

---

## 🚀 Boas Práticas

| ✅ Recomendado | ❌ Evitar |
|---|---|
| PRs pequenas e focadas | PRs gigantes com 100+ mudanças |
| Commits atômicos (um conceito por commit) | Commits com múltiplos conceitos misturados |
| Branches com nomes descritivos | Nomes genéricos (ex.: "branch1", "fix") |
| Sincronizar antes de criar PR | Submeter código obsoleto/desatualizado |
| Testar localmente antes de PR | Deixar testes falharem no CI |
| Documentação clara | Código sem comentários ou documentação |

---

## 📞 Dúvidas?

Verifique os commits recentes:
```bash
git log --oneline -10
```

Ou consulte a documentação do Git:
```bash
git help workflow
```

---

**Última atualização:** 12 de novembro de 2025

---

## 📦 Workflow adicional: `Run analyze_newicks` (GitHub Actions)

Adicionei um workflow executável manualmente em `.github/workflows/run_analyze_newicks.yml` que permite rodar o script `src/scripts/analyze_newicks.py` a partir da interface do GitHub (workflow_dispatch). Abaixo estão as instruções rápidas para incluir esse workflow via PR e executá-lo.

O que o workflow faz:
- Recebe inputs: `newicks_path` (obrigatório), `metadata` (opcional) e `var_mapping` (opcional).
- Instala dependências via `requirements.txt` (se existir).
- Executa: `python src/scripts/analyze_newicks.py <newicks_path> [metadata] [var_mapping]`.
- Publica os artefatos gerados (`clados_summary.csv`, `clados_summary.docx`, `clados_summary_plain_newicks.txt`) como artifacts do workflow.

Observações importantes:
- Runners públicos do GitHub Actions não têm acesso ao seu filesystem local. Se os `.newick` estiverem fora do repositório (por exemplo `/home/cristiano/...` no seu computador), o workflow em github.com não conseguirá acessá-los.
- Para executar com seus dados locais, use uma das opções abaixo:
  - Copiar os dados para dentro do repositório (diretório `data/` ou similar) e referenciar `newicks_path` relativo.
  - Usar um runner self-hosted (configurar um runner na sua máquina/servidor) e então disparar o workflow — o runner terá acesso ao seu filesystem local.
  - Fazer o upload dos arquivos `.newick` para um storage acessível (S3, GCS) e adaptar o workflow para baixar os dados antes da execução.

Como abrir uma PR que inclua o workflow
1. Criar branch a partir de `sandbox` (ou branch base adequada):
```bash
git checkout sandbox
git pull origin sandbox
git checkout -b feature/add-analyze-newicks-workflow
```
2. Adicionar o arquivo do workflow (já criado localmente em `.github/workflows/run_analyze_newicks.yml`) e commitar:
```bash
git add .github/workflows/run_analyze_newicks.yml
git commit -m "Adiciona workflow GitHub Actions: Run analyze_newicks (workflow_dispatch)"
git push origin feature/add-analyze-newicks-workflow
```
3. Criar PR apontando para `sandbox` como base. Na descrição da PR inclua:
   - Objetivo do workflow (executar `analyze_newicks.py` via Actions).
   - Observações sobre acesso a dados externos e sugestão para self-hosted runner se necessário.

Como executar o workflow (após merge ou em branch de PR)
1. No GitHub → Actions → selecione "Run analyze_newicks".
2. Clique em "Run workflow" (botão direito) e preencha os inputs:
   - `newicks_path`: caminho relativo (ex: `src/scripts`) ou absoluto (apenas em self-hosted runner).
   - `metadata`: (opcional) caminho para CSV de metadata.
   - `var_mapping`: (opcional) caminho para `var_mapping.csv`.
3. Aguarde a execução e baixe o artefato "analyze_newicks-results".

Se quiser, posso:
- Abrir o PR eu mesmo na sua branch (`feature/add-analyze-newicks-workflow`) e preparar a descrição da PR.
- Adicionar instruções no README com exemplos práticos e um pequeno script de preparação de dados para executar no Actions.
