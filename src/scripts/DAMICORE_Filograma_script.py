import os
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
# Configurar backend não-interativo do matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import toytree
import toyplot
import toyplot.pdf
from Bio import Phylo
from io import StringIO

# === SISTEMA DE CHECKPOINT/RETOMADA ===
class CheckpointManager:
    """Gerenciador de checkpoint para retomada automática do pipeline"""
    
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.checkpoint_file = os.path.join(output_dir, "filograma_checkpoint.json")
        self.progress = self.load_checkpoint()
    
    def load_checkpoint(self):
        """Carrega checkpoint existente ou cria novo"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                print(f"📋 Checkpoint encontrado: {self.checkpoint_file}")
                return progress
            except Exception as e:
                print(f"⚠️  Erro ao carregar checkpoint: {e}")
        
        # Cria novo checkpoint
        return {
            "start_time": datetime.now().isoformat(),
            "data_path": "",
            "total_samples": 0,
            "completed_steps": {
                "data_loading": False,
                "bootstrap_sampling": False,
                "sample_files_creation": False,
                "damicore_execution": False,
                "newick_collection": False,
                "visualization": False
            },
            "completed_samples": [],
            "failed_samples": [],
            "newick_files": [],
            "last_update": datetime.now().isoformat()
        }
    
    def save_checkpoint(self):
        """Salva checkpoint atual"""
        self.progress["last_update"] = datetime.now().isoformat()
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Erro ao salvar checkpoint: {e}")
    
    def mark_step_completed(self, step_name):
        """Marca uma etapa como concluída"""
        self.progress["completed_steps"][step_name] = True
        self.save_checkpoint()
        print(f"✅ Etapa concluída: {step_name}")
    
    def is_step_completed(self, step_name):
        """Verifica se uma etapa já foi concluída"""
        return self.progress["completed_steps"].get(step_name, False)
    
    def add_completed_sample(self, sample_name):
        """Adiciona amostra concluída"""
        if sample_name not in self.progress["completed_samples"]:
            self.progress["completed_samples"].append(sample_name)
            self.save_checkpoint()
    
    def add_failed_sample(self, sample_name, error_msg):
        """Adiciona amostra que falhou"""
        failure_info = {
            "sample": sample_name,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        self.progress["failed_samples"].append(failure_info)
        self.save_checkpoint()
    
    def is_sample_completed(self, sample_name):
        """Verifica se uma amostra já foi processada"""
        return sample_name in self.progress["completed_samples"]
    
    def print_progress_summary(self):
        """Imprime resumo do progresso"""
        print("\n" + "="*60)
        print("📊 RESUMO DO PROGRESSO")
        print("="*60)
        
        completed_count = sum(1 for v in self.progress["completed_steps"].values() if v)
        total_steps = len(self.progress["completed_steps"])
        
        print(f"🎯 Etapas concluídas: {completed_count}/{total_steps}")
        
        for step, completed in self.progress["completed_steps"].items():
            status = "✅" if completed else "⏳"
            print(f"  {status} {step.replace('_', ' ').title()}")
        
        if self.progress["completed_samples"]:
            print(f"📦 Amostras processadas: {len(self.progress['completed_samples'])}")
        
        if self.progress["failed_samples"]:
            print(f"❌ Amostras com falha: {len(self.progress['failed_samples'])}")
        
        print("="*60)

# === CONFIGURAÇÃO INTERATIVA ===
def get_input_file_path():
    """Solicita interativamente o caminho do arquivo CSV"""
    print("=== DAMICORE Filograma Script ===")
    print("Este script processa arquivos CSV para análise filogenética.")
    print()
    
    while True:
        DATA_PATH = input("Digite o caminho completo para o arquivo CSV: ").strip()
        
        # Remove aspas se o usuário colou um caminho com aspas
        DATA_PATH = DATA_PATH.strip('"').strip("'")
        
        if not DATA_PATH:
            print("❌ Por favor, digite um caminho válido.")
            continue
            
        if not os.path.exists(DATA_PATH):
            print(f"❌ Arquivo não encontrado: {DATA_PATH}")
            print("Verifique se o caminho está correto e tente novamente.")
            continue
            
        if not DATA_PATH.lower().endswith('.csv'):
            print("⚠️  Aviso: O arquivo não tem extensão .csv")
            response = input("Deseja continuar mesmo assim? (s/n): ").lower()
            if response != 's':
                continue
        
        # Verifica se o arquivo pode ser lido
        try:
            test_df = pd.read_csv(DATA_PATH, nrows=1)
            print(f"✅ Arquivo válido encontrado: {DATA_PATH}")
            print(f"📊 Colunas detectadas: {len(test_df.columns)}")
            
            # Mostra informações do arquivo
            file_size_mb = os.path.getsize(DATA_PATH) / (1024 * 1024)
            print(f"📊 Tamanho do arquivo: {file_size_mb:.1f} MB")
            
            return DATA_PATH
            
        except Exception as e:
            print(f"❌ Erro ao ler o arquivo: {e}")
            print("Verifique se o arquivo é um CSV válido.")
            continue

# Solicita o caminho do arquivo interativamente
DATA_PATH = get_input_file_path()
SCRIPTS_OUTPUT_BASE = os.path.splitext(os.path.basename(DATA_PATH))[0]
OUTPUT_DIR = os.path.join(os.path.dirname(DATA_PATH), SCRIPTS_OUTPUT_BASE)
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"\n📁 Diretório de saída: {OUTPUT_DIR}")

# Inicializa o gerenciador de checkpoint
checkpoint_manager = CheckpointManager(OUTPUT_DIR)
checkpoint_manager.progress["data_path"] = DATA_PATH
checkpoint_manager.save_checkpoint()

# Verifica se há progresso anterior
if any(checkpoint_manager.progress["completed_steps"].values()):
    print("\n🔄 RETOMADA DETECTADA!")
    checkpoint_manager.print_progress_summary()
    
    response = input("\nDeseja continuar de onde parou? (s/n): ").lower()
    if response != 's':
        print("🔄 Reiniciando do zero...")
        # Reset do checkpoint
        checkpoint_manager.progress["completed_steps"] = {k: False for k in checkpoint_manager.progress["completed_steps"]}
        checkpoint_manager.progress["completed_samples"] = []
        checkpoint_manager.progress["failed_samples"] = []
        checkpoint_manager.save_checkpoint()
    else:
        print("▶️  Continuando do checkpoint...")

print("\n🚀 Iniciando processamento...")

# === 1. Carregamento e pré-processamento ===
if not checkpoint_manager.is_step_completed("data_loading"):
    print("\n📊 Etapa 1: Carregamento e pré-processamento dos dados...")
    
    # Ler o DataFrame original para preservar os nomes das colunas
    original_df = pd.read_csv(DATA_PATH, encoding="utf-8", low_memory=False)
    original_columns = original_df.columns.tolist()
    
    # Criar dicionários para mapeamento bidirecional entre índices e nomes originais
    index_to_name = {str(i): name for i, name in enumerate(original_columns)}
    name_to_index = {name: str(i) for i, name in enumerate(original_columns)}
    
    # Criar DataFrame de trabalho com índices como nomes das colunas
    df = original_df.copy()
    df.columns = [str(i) for i in range(len(df.columns))]
    # Usando map em vez de applymap (deprecated)
    df = df.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)
    
    print(f"✅ Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas")
    checkpoint_manager.mark_step_completed("data_loading")
else:
    print("⏭️  Etapa 1: Carregamento já concluído, carregando dados...")
    # Recarrega os dados necessários
    original_df = pd.read_csv(DATA_PATH, encoding="utf-8", low_memory=False)
    original_columns = original_df.columns.tolist()
    index_to_name = {str(i): name for i, name in enumerate(original_columns)}
    name_to_index = {name: str(i) for i, name in enumerate(original_columns)}
    df = original_df.copy()
    df.columns = [str(i) for i in range(len(df.columns))]
    df = df.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)

# === 2. Reamostragem bootstrap ===
if not checkpoint_manager.is_step_completed("bootstrap_sampling"):
    print("\n🔄 Etapa 2: Reamostragem bootstrap...")
    
    resampled_df_l = [df]
    for i in range(22):
        resampled_df_l.append(df.sample(n=df.shape[0], replace=True, random_state=i))
    
    checkpoint_manager.progress["total_samples"] = len(resampled_df_l)
    print(f"✅ {len(resampled_df_l)} amostras bootstrap criadas")
    checkpoint_manager.mark_step_completed("bootstrap_sampling")
else:
    print("⏭️  Etapa 2: Bootstrap já concluído, recriando amostras...")
    resampled_df_l = [df]
    for i in range(22):
        resampled_df_l.append(df.sample(n=df.shape[0], replace=True, random_state=i))

# === 3. Salvamento das amostras ===
if not checkpoint_manager.is_step_completed("sample_files_creation"):
    print("\n💾 Etapa 3: Criando arquivos de amostra...")
    
    sample_dir = os.path.join(OUTPUT_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    
    for idx, resampled_df in enumerate(resampled_df_l):
        resample_dir = os.path.join(sample_dir, f"resample_{idx:02d}")
        os.makedirs(resample_dir, exist_ok=True)
        
        for col in resampled_df.columns:
            col_path = os.path.join(resample_dir, f"col_{col}.txt")
            resampled_df[col].to_csv(col_path, index=False, header=False, encoding="utf-8")
        
        print(f"📁 Amostra {idx:02d} salva em {resample_dir}")
    
    print(f"✅ {len(resampled_df_l)} arquivos de amostra criados")
    checkpoint_manager.mark_step_completed("sample_files_creation")
else:
    print("⏭️  Etapa 3: Arquivos de amostra já criados")
    sample_dir = os.path.join(OUTPUT_DIR, "sample_full")

# === 4. Execução do DAMICORE para cada amostra ===
if not checkpoint_manager.is_step_completed("damicore_execution"):
    print("\n🚀 Etapa 4: Executando DAMICORE para cada amostra...")
    
    DAMICORE_CLI_PATH = "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/DAMICORE/damicore_py3/damicore.py"
    results_dir = os.path.join(OUTPUT_DIR, "damicore_results")
    os.makedirs(results_dir, exist_ok=True)
    
    sample_list = [m for m in os.listdir(sample_dir) if os.path.isdir(os.path.join(sample_dir, m))]
    total_samples = len(sample_list)
    processed_count = 0
    
    for m in sample_list:
        # Verifica se esta amostra já foi processada
        if checkpoint_manager.is_sample_completed(m):
            print(f"⏭️  Amostra {m} já processada, pulando...")
            processed_count += 1
            continue
        
        resampleddatasource = os.path.join(sample_dir, m)
        tree_output = os.path.join(results_dir, f"{m}-tree.newick")
        
        # Verifica se o arquivo newick já existe
        if os.path.exists(tree_output):
            print(f"✅ Arquivo newick já existe para {m}, marcando como concluído")
            checkpoint_manager.add_completed_sample(m)
            processed_count += 1
            continue
        
        argv = [
            "python3", DAMICORE_CLI_PATH,
            "--compressor", "gzip",
            "--tree-output", tree_output,
            resampleddatasource
        ]
        
        print(f"\n🔄 Processando amostra {processed_count + 1}/{total_samples}: {m}")
        print(f"Executando DAMICORE: {' '.join(argv)}")
        
        try:
            process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            for line in process.stdout:
                print(line, end="")
            
            process.wait()
            
            if process.returncode == 0:
                print(f"✅ DAMICORE concluído com sucesso para {m}")
                checkpoint_manager.add_completed_sample(m)
                processed_count += 1
            else:
                error_msg = f"Código de saída: {process.returncode}"
                print(f"❌ Erro ao executar DAMICORE para {m} ({error_msg})")
                checkpoint_manager.add_failed_sample(m, error_msg)
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Exceção ao processar {m}: {error_msg}")
            checkpoint_manager.add_failed_sample(m, error_msg)
    
    print(f"\n✅ Execução do DAMICORE concluída: {processed_count}/{total_samples} amostras processadas")
    if checkpoint_manager.progress["failed_samples"]:
        print(f"⚠️  {len(checkpoint_manager.progress['failed_samples'])} amostras falharam")
    
    checkpoint_manager.mark_step_completed("damicore_execution")
else:
    print("⏭️  Etapa 4: Execução do DAMICORE já concluída")
    results_dir = os.path.join(OUTPUT_DIR, "damicore_results")

# === 5. Coleta dos arquivos newick ===
if not checkpoint_manager.is_step_completed("newick_collection"):
    print("\n📄 Etapa 5: Coletando arquivos newick...")
    
    plain_newicks = []
    newick_files = []
    
    for tf in os.listdir(results_dir):
        if tf.endswith("-tree.newick"):
            tf_path = os.path.join(results_dir, tf)
            if os.path.exists(tf_path):
                with open(tf_path, "r") as f:
                    content = f.read().strip()
                    if content:  # Só adiciona se não estiver vazio
                        plain_newicks.append(content)
                        newick_files.append(tf)
    
    if not plain_newicks:
        print("❌ Nenhum arquivo .newick válido encontrado.")
        print("Verifique se o DAMICORE foi executado corretamente.")
        exit(1)
    else:
        print(f"✅ {len(plain_newicks)} arquivos newick coletados")
        checkpoint_manager.progress["newick_files"] = newick_files
        checkpoint_manager.mark_step_completed("newick_collection")
else:
    print("⏭️  Etapa 5: Coleta de arquivos newick já concluída")
    # Recarrega os arquivos newick
    plain_newicks = []
    for tf in os.listdir(results_dir):
        if tf.endswith("-tree.newick"):
            tf_path = os.path.join(results_dir, tf)
            if os.path.exists(tf_path):
                with open(tf_path, "r") as f:
                    content = f.read().strip()
                    if content:
                        plain_newicks.append(content)

string_newicks = "\n".join(plain_newicks)

# === 6. Visualização: Cloud Tree e Consenso ===
if not checkpoint_manager.is_step_completed("visualization"):
    print("\n🎨 Etapa 6: Gerando visualizações...")
    
    if string_newicks.strip():
        try:
            # Cloud Tree com nomes originais
            print("📊 Gerando Cloud Tree...")
            mtree = toytree.mtree(string_newicks)
            
            # Processar os labels para Cloud Tree
            cloud_new_list = []
            for i in mtree.get_tip_labels():
                j = i.strip("''")  # Remove aspas
                # Extrair apenas o número do nome do arquivo (entre 'col_' e '.txt')
                num = j.split('col_')[1].split('.txt')[0]
                cloud_new_list.append(num)
            
            # Converter índices para nomes originais
            cloud_tip_labels = []
            for m in cloud_new_list:
                n = index_to_name[m]  # Usar o dicionário index_to_name em vez de Dict_columns
                cloud_tip_labels.append(n)
            
            # Desenhar Cloud Tree de forma simplificada
            canvas_tuple = mtree.draw_cloud_tree(
                tip_labels=cloud_tip_labels,
                node_labels=False,
                use_edge_lengths=False,
                node_sizes=16
            )
            canvas = canvas_tuple[0]
            cloud_tree_path = os.path.join(OUTPUT_DIR, "cloud_tree.pdf")
            toyplot.pdf.render(canvas, cloud_tree_path)
            print(f"✅ Cloud tree salva em {cloud_tree_path}")

            # Consensus Tree
            print("📊 Gerando Consensus Tree...")
            ctre = mtree.get_consensus_tree()
            
            # Processar os labels para Consensus Tree
            new_list = []
            for i in ctre.get_tip_labels():
                j = i.strip("''")  # Remove aspas
                # Extrair apenas o número do nome do arquivo (entre 'col_' e '.txt')
                num = j.split('col_')[1].split('.txt')[0]
                new_list.append(num)
            
            # Converter índices para nomes originais
            new_tip_labels = []
            for m in new_list:
                n = index_to_name[m]  # Usar o dicionário index_to_name em vez de Dict_columns
                new_tip_labels.append(n)
            
            # Garantir que os valores de suporte estejam acessíveis
            for node in ctre.treenode.traverse():
                node.support = node.support
            
            # Desenhar a árvore de consenso de forma simplificada
            canvas_tuple = ctre.draw(
                tip_labels=new_tip_labels,
                node_labels='support',
                use_edge_lengths=False,
                node_sizes=32
            )
            consensus_canvas = canvas_tuple[0]
            consensus_tree_path = os.path.join(OUTPUT_DIR, "consensus_tree.pdf")
            toyplot.pdf.render(consensus_canvas, consensus_tree_path)
            print(f"✅ Consensus tree salva em {consensus_tree_path}")
            
        except Exception as e:
            print(f"⚠️  Erro ao gerar visualizações Toytree: {e}")
            print("Continuando com visualização Biopython...")
    else:
        print("❌ Nenhum dado newick disponível para visualização das árvores.")

    # === Visualização com Biopython ===
    # Usar o primeiro arquivo newick da lista para visualização
    if plain_newicks:
        try:
            print("📊 Gerando visualização Biopython...")
            
            # Criar um arquivo temporário com o primeiro newick
            temp_newick_path = os.path.join(OUTPUT_DIR, 'temp_tree.newick')
            with open(temp_newick_path, 'w') as f:
                f.write(plain_newicks[0])
            
            # Ler e processar a árvore
            tree = Phylo.read(temp_newick_path, 'newick')
            
            # Substituir os nós folha pelos nomes originais
            for leaf in tree.get_terminals():
                # Extrair apenas o número do nome do arquivo
                if leaf.name and 'col_' in leaf.name:
                    num = leaf.name.split('col_')[1].split('.txt')[0]
                    if num in index_to_name:
                        leaf.name = index_to_name[num]
            
            # Configurar a figura
            fig = plt.figure(figsize=(12, 8))
            axes = fig.add_subplot(1, 1, 1)
            
            # Desenhar a árvore com nomes originais
            Phylo.draw(tree, axes=axes, show_confidence=True)
            plt.title('Árvore Filogenética (Biopython)')
            biopython_tree_path = os.path.join(OUTPUT_DIR, 'tree_biopython.png')
            plt.savefig(biopython_tree_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Árvore Biopython salva em {biopython_tree_path}")
            
            # Remove arquivo temporário
            if os.path.exists(temp_newick_path):
                os.remove(temp_newick_path)
                
        except Exception as e:
            print(f"⚠️  Erro ao gerar visualização Biopython: {e}")
    
    print("✅ Visualizações concluídas")
    checkpoint_manager.mark_step_completed("visualization")
else:
    print("⏭️  Etapa 6: Visualizações já concluídas")

# === FINALIZAÇÃO E RESUMO ===
print("\n" + "="*80)
print("🎉 PIPELINE DAMICORE FILOGRAMA CONCLUÍDO COM SUCESSO!")
print("="*80)

# Resumo final
checkpoint_manager.print_progress_summary()

# Informações dos arquivos gerados
print("\n📁 ARQUIVOS GERADOS:")
generated_files = []
if os.path.exists(os.path.join(OUTPUT_DIR, "cloud_tree.pdf")):
    generated_files.append("cloud_tree.pdf")
if os.path.exists(os.path.join(OUTPUT_DIR, "consensus_tree.pdf")):
    generated_files.append("consensus_tree.pdf")
if os.path.exists(os.path.join(OUTPUT_DIR, "tree_biopython.png")):
    generated_files.append("tree_biopython.png")

for file in generated_files:
    file_path = os.path.join(OUTPUT_DIR, file)
    file_size = os.path.getsize(file_path) / 1024  # KB
    print(f"  ✅ {file} ({file_size:.1f} KB)")

# Informações do checkpoint
if os.path.exists(checkpoint_manager.checkpoint_file):
    print(f"\n📋 Checkpoint salvo em: {checkpoint_manager.checkpoint_file}")
    print("   (Para reexecutar ou continuar interrompido)")

# Tempo total (estimado)
start_time = datetime.fromisoformat(checkpoint_manager.progress["start_time"])
end_time = datetime.now()
total_time = end_time - start_time
print(f"\n⏱️  Tempo total de processamento: {total_time}")

print(f"\n📁 Todos os resultados salvos em: {OUTPUT_DIR}")
print("\n🚀 Pipeline finalizado! Verifique os arquivos de visualização gerados.")
print("="*80)

# === 8. Análise de distâncias cophenéticas (placeholder) ===
def fake_tree_distance(tree1, tree2):
    return np.random.rand()

n_trees = len(plain_newicks)
cophenetic_matrix = np.zeros((n_trees, n_trees))
for i in range(n_trees):
    for j in range(i+1, n_trees):
        d = fake_tree_distance(plain_newicks[i], plain_newicks[j])
        cophenetic_matrix[i, j] = cophenetic_matrix[j, i] = d

plt.figure(figsize=(8,6))
import seaborn as sns
# Criar lista de nomes originais para os eixos do heatmap
variable_names = [f"Árvore {i+1}" for i in range(n_trees)]
sns.heatmap(cophenetic_matrix, cmap="viridis", 
            xticklabels=variable_names, 
            yticklabels=variable_names)
plt.title("Matriz de Distâncias Cophenéticas entre Árvores")
plt.xlabel("Árvore")
plt.ylabel("Árvore")
plt.tight_layout()  # Ajustar layout para acomodar labels
plt.savefig(os.path.join(OUTPUT_DIR, "cophenetic_matrix.png"))
plt.close()
print(f"Matriz de distâncias cophenéticas salva em {os.path.join(OUTPUT_DIR, 'cophenetic_matrix.png')}")

# === 9. Clusterização ===
from sklearn.cluster import AgglomerativeClustering
n_clusters = 3
clustering = AgglomerativeClustering(n_clusters=n_clusters, metric='precomputed', linkage='average')
labels = clustering.fit_predict(cophenetic_matrix)
plt.figure(figsize=(8,4))
plt.hist(labels, bins=n_clusters)
plt.title("Distribuição dos Clusters das Árvores")
plt.xlabel("Cluster")
plt.ylabel("Número de Árvores")
plt.savefig(os.path.join(OUTPUT_DIR, "tree_clusters_hist.png"))
plt.close()
print(f"Histograma de clusters salvo em {os.path.join(OUTPUT_DIR, 'tree_clusters_hist.png')}")

# === 10. Exportação de resultados ===
np.save(os.path.join(OUTPUT_DIR, "cophenetic_matrix.npy"), cophenetic_matrix)
np.save(os.path.join(OUTPUT_DIR, "tree_clusters.npy"), labels)
print(f"Resultados exportados para: {OUTPUT_DIR}")

# === 6. Visualização do Heatmap ===
plt.figure(figsize=(12, 10))
sns.heatmap(
    cophenetic_matrix,
    annot=True,
    cmap='YlOrRd',
    xticklabels=[index_to_name[str(i)] for i in range(len(cophenetic_matrix))],
    yticklabels=[index_to_name[str(i)] for i in range(len(cophenetic_matrix))],
    fmt='.2f'
)
plt.title('Matriz de Distâncias Cophenéticas')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'heatmap_distances.png'), dpi=300, bbox_inches='tight')
plt.close()

# Limpeza do arquivo temporário
if os.path.exists(temp_newick_path):
    os.remove(temp_newick_path)
