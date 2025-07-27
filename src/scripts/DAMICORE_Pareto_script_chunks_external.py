"""
DAMICORE + Análise de Pareto - Versão Otimizada para Arquivos Grandes (Drive Externo)

Esta versão foi adaptada para processar arquivos CSV muito grandes (15GB+) sem estouro de memória,
utilizando processamento em chunks (lotes) e salvando todos os resultados em drive externo.

CONFIGURAÇÃO PARA DRIVE EXTERNO:
- Modifique a variável EXTERNAL_DRIVE_PATH para o ponto de montagem do seu drive externo
- O script detectará automaticamente o drive ou permitirá configuração manual
- Todos os arquivos temporários e resultados serão salvos no drive externo

Para arquivos menores (< 5GB), use a versão original: DAMICORE_Pareto_script.py

Parâmetros configuráveis:
- chunk_size: Tamanho dos chunks (padrão: 100.000 linhas)
- EXTERNAL_DRIVE_PATH: Caminho para o drive externo

Autor: DAMICORE Team
Data: 2025
"""

import os
import pandas as pd
import numpy as np
import ast
from statistics import multimode
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import toytree
import toyplot
import toyplot.pdf
from Bio import Phylo
from large_file_processor import process_large_file_without_pandas

# ============================================================================
# CONFIGURAÇÃO DO DRIVE EXTERNO
# ============================================================================

def get_damicore_path():
    """
    🔧 Obtém o caminho relativo portável para o DAMICORE.
    
    Returns:
        str: Caminho absoluto para o damicore.py
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # /DAMICORE/src
    damicore_path = os.path.join(project_root, "damicore.py")
    
    # Fallback para estrutura alternativa (damicore_py3)
    if not os.path.exists(damicore_path):
        alt_path = os.path.join(os.path.dirname(project_root), "damicore_py3", "damicore.py")
        if os.path.exists(alt_path):
            damicore_path = alt_path
        else:
            print(f"⚠️ Aviso: DAMICORE não encontrado em {damicore_path} ou {alt_path}")
    
    return damicore_path


def detect_external_drive():
    """Detecta automaticamente drives externos montados"""
    media_path = f"/media/{os.getenv('USER', 'user')}/"
    if os.path.exists(media_path):
        drives = [d for d in os.listdir(media_path) if os.path.isdir(os.path.join(media_path, d))]
        if drives:
            return os.path.join(media_path, drives[0])
    return None

def get_external_drive_path():
    """Obtém o caminho do drive externo"""
    # Tenta detectar automaticamente
    auto_drive = detect_external_drive()
    if auto_drive:
        print(f"Drive externo detectado automaticamente: {auto_drive}")
        response = input(f"Usar este drive? (s/n): ").lower()
        if response == 's':
            return auto_drive
    
    # Configuração manual
    print("\nDrives externos comuns:")
    print("- /media/seu_usuario/nome_do_drive")
    print("- /mnt/external_drive")
    print("- /run/media/seu_usuario/nome_do_drive")
    
    while True:
        drive_path = input("\nDigite o caminho completo do drive externo: ").strip()
        if os.path.exists(drive_path) and os.path.isdir(drive_path):
            # Testa se é possível escrever
            test_file = os.path.join(drive_path, "test_write_permission.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return drive_path
            except:
                print(f"❌ Erro: Não é possível escrever em {drive_path}")
        else:
            print(f"❌ Erro: Caminho {drive_path} não existe ou não é um diretório")

# ============================================================================
# CONFIGURAÇÃO PRINCIPAL
# ============================================================================

def main():
    # Configuração do drive externo
    print("=== CONFIGURAÇÃO DO DRIVE EXTERNO ===")
    EXTERNAL_DRIVE_PATH = get_external_drive_path()
    print(f"✅ Drive externo configurado: {EXTERNAL_DRIVE_PATH}")
    
    # Verifica espaço disponível
    statvfs = os.statvfs(EXTERNAL_DRIVE_PATH)
    free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
    print(f"📊 Espaço livre no drive externo: {free_space_gb:.1f} GB")
    
    if free_space_gb < 50:
        print("⚠️  AVISO: Espaço livre menor que 50GB pode ser insuficiente para arquivos grandes")
        response = input("Continuar mesmo assim? (s/n): ").lower()
        if response != 's':
            print("Operação cancelada.")
            return

    # Solicita o arquivo CSV
    print("\n=== CONFIGURAÇÃO DO ARQUIVO CSV ===")
    input_path = input("Digite o caminho completo do arquivo CSV: ").strip()
    
    if not os.path.exists(input_path):
        print(f"❌ Erro: Arquivo {input_path} não encontrado")
        return
    
    # Verifica tamanho do arquivo
    file_size_gb = os.path.getsize(input_path) / (1024**3)
    print(f"📁 Tamanho do arquivo: {file_size_gb:.1f} GB")
    
    if file_size_gb * 3 > free_space_gb:
        print(f"⚠️  AVISO: Recomenda-se pelo menos {file_size_gb*3:.1f} GB livres (3x o tamanho do arquivo)")
        response = input("Continuar mesmo assim? (s/n): ").lower()
        if response != 's':
            print("Operação cancelada.")
            return

    # Configuração dos diretórios de saída no drive externo
    SCRIPTS_OUTPUT_BASE = os.path.splitext(os.path.basename(input_path))[0]
    OUTPUT_DIR = os.path.join(EXTERNAL_DRIVE_PATH, "DAMICORE_RESULTS", SCRIPTS_OUTPUT_BASE)
    DAMICORE_DIR = os.path.join(OUTPUT_DIR, "damicore_analysis")
    os.makedirs(DAMICORE_DIR, exist_ok=True)
    
    print(f"📂 Resultados serão salvos em: {OUTPUT_DIR}")

    # === 1. Carregamento e pré-processamento ===
    print("\n=== INICIANDO PROCESSAMENTO ===")
    print("Carregando dados em chunks ultra-pequenos para arquivos grandes...")
    
    # Configuração Adaptativa Otimizada V2 (baseada em testes reais + sugestão do usuário)
    # NOVA ABORDAGEM: Menos linhas por chunk, mas TODAS as colunas de uma vez
    # Resultados dos testes originais:
    # - chunk_size=100: 18 linhas/s, 1.1GB RAM ✅ ESTÁVEL
    # - chunk_size=500: 30 linhas/s, 3.6GB RAM ✅ ÓTIMO BALANCE
    # - chunk_size=1000: 29 linhas/s, 6.3GB RAM ⚠️ LIMITE CRÍTICO
    # - chunk_size=5000: OOM/Killed ❌ FALHA
    
    if file_size_gb >= 10:
        # Para arquivos ultra-grandes (>=10GB): chunks menores, todas as colunas
        chunk_size = 100     # ULTRA-CONSERVADOR: máxima estabilidade (18 linhas/s, 1.1GB)
        bootstrap_samples = 2  # Reduzido para economizar tempo
        max_columns_per_batch = None  # TODAS AS COLUNAS de uma vez!
        print("🚀 MODO ULTRA-OTIMIZADO para arquivo >=10GB (todas as colunas por chunk)")
    elif file_size_gb >= 5:
        # Para arquivos grandes (5-10GB): configuração balanceada
        chunk_size = 200     # Chunks pequenos, todas as colunas
        bootstrap_samples = 3
        max_columns_per_batch = None  # TODAS AS COLUNAS
        print("⚖️  MODO BALANCEADO para arquivo 5-10GB (todas as colunas)")
    elif file_size_gb >= 1:
        # Para arquivos médios (1-5GB): performance otimizada
        chunk_size = 500     # Chunks médios, todas as colunas
        bootstrap_samples = 5
        max_columns_per_batch = None  # TODAS AS COLUNAS
        print("⚡ MODO PERFORMANCE para arquivo 1-5GB (todas as colunas)")
    else:
        # Para arquivos pequenos (<1GB): configuração tradicional
        chunk_size = 2_000   # Chunks grandes, todas as colunas
        bootstrap_samples = 10
        max_columns_per_batch = None  # TODAS AS COLUNAS
        print("🏃 MODO RÁPIDO para arquivo <1GB (todas as colunas)")
    
    columns_msg = "TODAS as colunas" if max_columns_per_batch is None else f"{max_columns_per_batch} colunas por lote"
    print(f"📊 Configuração Adaptativa V2: chunk_size={chunk_size:,}, bootstrap_samples={bootstrap_samples}, processamento={columns_msg}")
    
    if file_size_gb >= 10:
        print("📈 Nova estratégia otimizada:")
        print(f"   - Chunks MENORES: {chunk_size} linhas (máxima estabilidade: 1.1GB RAM)")
        print("   - Processamento: TODAS as 101 colunas de uma vez")
        print(f"   - Bootstrap otimizado: {bootstrap_samples} amostras")
        print("   - Elimina complexidade de lotes de colunas")
        print("   - Mais fiel ao comportamento original do DAMICORE")
    
    # Inicialização das estruturas (necessário para ambos os modos)
    sample_dir = os.path.join(DAMICORE_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    
    # Para arquivos muito grandes, usa processamento STREAMING
    if file_size_gb >= 10:
        print("🌊 Usando processamento STREAMING (1 chunk por vez) para arquivo muito grande...")
        from streaming_processor import process_file_streaming
        
        # Processa arquivo em modo streaming
        newick_files = process_file_streaming(
            input_path, chunk_size, bootstrap_samples, max_columns_per_batch,
            sample_dir, DAMICORE_DIR, EXTERNAL_DRIVE_PATH
        )
        
        # Pula para visualizações (não precisa do loop principal)
        print(f"\n=== RESULTADOS DO STREAMING ===")
        print(f"Total de arquivos newick coletados: {len(newick_files)}")
        
        if len(newick_files) == 0:
            print("❌ Nenhum arquivo newick encontrado. Verifique se o DAMICORE foi executado corretamente.")
            return
        
        # Vai direto para as visualizações
        from visualization_helper import generate_visualizations
        generate_visualizations(newick_files, DAMICORE_DIR)
        
        print(f"\n✅ Análise DAMICORE STREAMING concluída com sucesso!")
        print(f"📂 Todos os resultados foram salvos em: {OUTPUT_DIR}")
        
        # Análise de Pareto (opcional)
        try:
            response = input("\nDeseja realizar a análise de Fronteira de Pareto? (s/n): ")
            if response.lower() == 's':
                print("Análise de Pareto não implementada para modo streaming.")
        except EOFError:
            print("Análise de Pareto pulada (entrada não disponível).")
        
        print("Processamento streaming concluído com sucesso!")
        return
    else:
        # Configuração otimizada do pandas para arquivos menores
        chunk_iter = pd.read_csv(
            input_path, 
            encoding="utf-8", 
            low_memory=True,
            chunksize=chunk_size,
            engine='c',
            memory_map=True,
            dtype=str
        )

    # Inicialização das estruturas
    original_columns = None
    index_to_name = None
    name_to_index = None
    resampled_df_l = []
    chunk_idx = 0
    sample_dir = os.path.join(DAMICORE_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)

    for chunk in chunk_iter:
        print(f"Processando chunk {chunk_idx} ({len(chunk)} linhas)...")
        
        if original_columns is None:
            original_columns = chunk.columns.tolist()
            index_to_name = {str(i): name for i, name in enumerate(original_columns)}
            name_to_index = {name: str(i) for i, name in enumerate(original_columns)}
        
        # Reindexa colunas
        chunk.columns = [str(i) for i in range(len(chunk.columns))]
        chunk = chunk.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)

        # Bootstrap no chunk com configuração adaptativa
        resampled_chunks = [chunk.copy()]  # Cópia explícita
        
        # Gera amostras bootstrap com limpeza de memória
        for i in range(bootstrap_samples):
            bootstrap_sample = chunk.sample(n=chunk.shape[0], replace=True, random_state=i)
            resampled_chunks.append(bootstrap_sample)
            
        # Libera memória do chunk original imediatamente
        del chunk
        import gc
        gc.collect()
        
        # Salva as colunas de cada chunk e amostra com otimização de memória
        for idx, resampled_df in enumerate(resampled_chunks):
            resample_dir = os.path.join(sample_dir, f"chunk_{chunk_idx}_resample_{idx:02d}")
            os.makedirs(resample_dir, exist_ok=True)
            
            # Processa colunas em lotes ULTRA-PEQUENOS para economizar memória
            columns = list(resampled_df.columns)
            
            # Usa configuração adaptativa para tamanho do lote
            if file_size_gb >= 10:
                batch_size = max_columns_per_batch  # Apenas 5 colunas por vez para arquivos grandes
            else:
                batch_size = 10
            
            print(f"    📝 Processando {len(columns)} colunas em lotes de {batch_size}...")
            
            for i in range(0, len(columns), batch_size):
                col_batch = columns[i:i+batch_size]
                print(f"      🔄 Lote {i//batch_size + 1}: colunas {i} a {min(i+batch_size-1, len(columns)-1)}")
                
                for col in col_batch:
                    col_path = os.path.join(resample_dir, f"col_{col}.txt")
                    # Usa método mais eficiente para salvar
                    with open(col_path, 'w', encoding='utf-8') as f:
                        for value in resampled_df[col]:
                            f.write(f"{value}\n")
                
                # Força limpeza de memória a cada lote
                import gc
                gc.collect()
                
                # Para arquivos muito grandes, pausa entre lotes
                if file_size_gb >= 10:
                    import time
                    time.sleep(0.1)  # Pequena pausa para liberar recursos
            
            print(f"  ✅ Chunk {chunk_idx}, amostra {idx}: {len(columns)} colunas salvas")

            # Executa DAMICORE para cada amostra com otimizações
            tree_output_path = os.path.join(DAMICORE_DIR, "damicore_results", f"chunk_{chunk_idx}_resample_{idx:02d}-tree.newick")
            os.makedirs(os.path.dirname(tree_output_path), exist_ok=True)
            
            cmd = [
                "python", "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/DAMICORE/damicore_py3/damicore.py",
                "--compressor", "gzip",
                "--serial",  # Força modo serial para evitar problemas de multiprocessing
                "--tree-output", tree_output_path,
                resample_dir
            ]
            
            print(f"  🔄 Executando DAMICORE para chunk {chunk_idx}, amostra {idx}...")
            try:
                # Executa com timeout para evitar travamentos
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True,
                    timeout=7200  # 2 horas de timeout
                )
                print(f"  ✅ DAMICORE executado com sucesso!")
            except subprocess.TimeoutExpired:
                print(f"  ⚠️  DAMICORE timeout para chunk {chunk_idx}, amostra {idx}")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Erro ao executar DAMICORE: {e}")
                if len(e.stdout) < 500:  # Limita output para economizar memória
                    print(f"  Stdout: {e.stdout}")
                if len(e.stderr) < 500:
                    print(f"  Stderr: {e.stderr}")
            
            # Libera memória após cada execução DAMICORE
            import gc
            gc.collect()

        # Libera memória de todas as amostras processadas
        for df in resampled_chunks:
            del df
        del resampled_chunks
        import gc
        gc.collect()
        
        chunk_idx += 1
        
        # Mostra progresso e uso de memória
        print(f"📊 Chunk {chunk_idx-1} processado. Memória liberada.")
        
        # A cada 10 chunks, força limpeza mais agressiva
        if chunk_idx % 10 == 0:
            print(f"🧹 Limpeza agressiva de memória após {chunk_idx} chunks...")
            gc.collect()
            
        # Verifica espaço livre no drive externo periodicamente
        if chunk_idx % 5 == 0:
            free_space_current = (os.statvfs(EXTERNAL_DRIVE_PATH).f_frsize * os.statvfs(EXTERNAL_DRIVE_PATH).f_bavail) / (1024**3)
            print(f"💾 Espaço livre atual no drive: {free_space_current:.1f} GB")

    # === 2. Consolidação dos dados dos chunks ===
    print("\n=== CONSOLIDANDO DADOS DOS CHUNKS ===")
    
    # Nova abordagem: consolidar dados de todos os chunks para cada amostra bootstrap
    # e depois executar DAMICORE individualmente para cada amostra (como no Filograma_script)
    consolidated_sample_dir = os.path.join(DAMICORE_DIR, "consolidated_samples")
    os.makedirs(consolidated_sample_dir, exist_ok=True)
    
    # Coleta todos os arquivos de dados dos chunks
    all_sample_dirs = []
    for item in os.listdir(sample_dir):
        item_path = os.path.join(sample_dir, item)
        if os.path.isdir(item_path):
            all_sample_dirs.append(item_path)
    
    print(f"Encontrados {len(all_sample_dirs)} diretórios de amostras para consolidar")
    
    # Consolidar dados por amostra bootstrap
    bootstrap_count = 0
    for sample_path in all_sample_dirs:
        if "resample_00" in sample_path:  # Apenas as amostras originais (não bootstrap)
            bootstrap_count += 1
    
    print(f"Consolidando {bootstrap_count} amostras bootstrap...")
    
    # Para cada índice de bootstrap, consolida dados de todos os chunks
    for bootstrap_idx in range(min(bootstrap_samples + 1, bootstrap_count)):  # +1 para incluir amostra original
        consolidated_resample_dir = os.path.join(consolidated_sample_dir, f"resample_{bootstrap_idx:02d}")
        os.makedirs(consolidated_resample_dir, exist_ok=True)
        
        # Consolida dados de todos os chunks para esta amostra bootstrap
        for col_idx in range(len(original_columns)):
            col_name = str(col_idx)
            consolidated_col_path = os.path.join(consolidated_resample_dir, f"col_{col_name}.txt")
            
            # Combina dados desta coluna de todos os chunks
            with open(consolidated_col_path, 'w', encoding='utf-8') as out_file:
                for sample_path in all_sample_dirs:
                    if f"resample_{bootstrap_idx:02d}" in sample_path:
                        col_file_path = os.path.join(sample_path, f"col_{col_name}.txt")
                        if os.path.exists(col_file_path):
                            with open(col_file_path, 'r', encoding='utf-8') as in_file:
                                out_file.write(in_file.read())
        
        print(f"  ✅ Amostra bootstrap {bootstrap_idx} consolidada")
    
    # === 3. Execução individual do DAMICORE para cada amostra bootstrap ===
    print("\n=== EXECUTANDO DAMICORE PARA CADA AMOSTRA BOOTSTRAP ===")
    
    # Executa DAMICORE individualmente para cada amostra bootstrap (como no Filograma_script)
    results_dir = os.path.join(DAMICORE_DIR, "damicore_results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Processar cada amostra bootstrap individualmente
    for resample_dir_name in os.listdir(consolidated_sample_dir):
        resample_path = os.path.join(consolidated_sample_dir, resample_dir_name)
        if not os.path.isdir(resample_path):
            continue
            
        print(f"\n🌳 Processando {resample_dir_name}...")
        
        # Definir arquivo de saída newick para esta amostra
        tree_output = os.path.join(results_dir, f"{resample_dir_name}-tree.newick")
        
        try:
            cmd = [
                "python", get_damicore_path(),
                "--compressor", "gzip",
                "--tree-output", tree_output,
                resample_path
            ]
            
            print(f"Executando: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)  # 2 horas timeout
            
            if result.returncode == 0:
                print(f"✅ {resample_dir_name}: DAMICORE executado com sucesso!")
            else:
                print(f"❌ {resample_dir_name}: Erro no DAMICORE: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"❌ {resample_dir_name}: DAMICORE timeout após 30 minutos")
        except Exception as e:
            print(f"❌ {resample_dir_name}: Erro ao executar DAMICORE: {e}")
    
    # === 4. Coleta dos arquivos newick (agora consistentes) ===
    print("\n=== COLETANDO ARQUIVOS NEWICK ===")
    newick_files = []
    
    if os.path.exists(results_dir):
        for file in os.listdir(results_dir):
            if file.endswith(".newick"):
                newick_files.append(os.path.join(results_dir, file))
    
    print(f"Total de arquivos newick coletados: {len(newick_files)}")

    if len(newick_files) == 0:
        print("❌ Nenhum arquivo newick encontrado após consolidação.")
        return []

    # === 5. Geração das visualizações finais ===
    print("\n=== GERANDO VISUALIZAÇÕES FINAIS ===")
    
    # Usar o helper de visualização com os dados consolidados
    from visualization_helper import generate_visualizations, create_index_to_name_mapping
    
    # Criar o mapeamento index_to_name
    if original_columns:
        # Criar um DataFrame temporário para gerar o mapeamento
        import pandas as pd
        temp_df = pd.DataFrame(columns=original_columns)
        index_to_name = create_index_to_name_mapping(temp_df)
        
        # Gerar visualizações usando o helper
        generate_visualizations(newick_files, DAMICORE_DIR, index_to_name)
    else:
        # Fallback sem mapeamento
        generate_visualizations(newick_files, DAMICORE_DIR)
    
    return newick_files


def old_visualization_code():
    """Código antigo de visualização mantido para referência"""
    # Consensus tree
    consensus_tree_path = "placeholder"
    try:
        consensus = mtre.get_consensus_tree()
        canvas = toyplot.Canvas(width=800, height=600)
        consensus.draw(
            node_labels=True,
            node_sizes=8,
            edge_widths=2,
            axes=canvas
        )
        toyplot.pdf.render(canvas, consensus_tree_path)
        print(f"Consensus tree salva em {consensus_tree_path}")
    except Exception as e:
        print(f"Erro ao gerar consensus tree: {e}")

    print(f"\n✅ Análise DAMICORE concluída com sucesso!")
    print(f"📂 Todos os resultados foram salvos em: {OUTPUT_DIR}")
    print(f"📊 Espaço final livre no drive: {(os.statvfs(EXTERNAL_DRIVE_PATH).f_frsize * os.statvfs(EXTERNAL_DRIVE_PATH).f_bavail) / (1024**3):.1f} GB")

    # Análise de Pareto (opcional)
    try:
        response = input("\nDeseja realizar a análise de Fronteira de Pareto? (s/n): ")
        if response.lower() == 's':
            print("Iniciando análise de Pareto...")
            # Aqui seria implementada a análise de Pareto se necessário
            print("Análise de Pareto não implementada nesta versão.")
    except EOFError:
        print("Análise de Pareto pulada (entrada não disponível).")

    print("Todas as análises foram concluídas com sucesso!")

def execute_chunk_processing(input_path, file_size_gb, OUTPUT_DIR, DAMICORE_DIR):
    """
    Executa o processamento em chunks do arquivo CSV.
    """
    print("\n=== INICIANDO PROCESSAMENTO ===")
    print("Carregando dados em chunks ultra-pequenos para arquivos grandes...")
    
    # Configuração ULTRA-RADICAL para arquivos muito grandes
    if file_size_gb >= 10:
        chunk_size = 100     # ULTRA-PEQUENO: apenas 100 linhas por chunk
        bootstrap_samples = 1  # Apenas 1 amostra bootstrap para economizar memória
        max_columns_per_batch = 5  # Processa apenas 5 colunas por vez
    elif file_size_gb >= 5:
        chunk_size = 500     # Chunks muito pequenos
        bootstrap_samples = 2
        max_columns_per_batch = 10
    else:
        chunk_size = 5_000   # Para arquivos menores
        bootstrap_samples = 3
        max_columns_per_batch = 20
    
    print(f"📊 Configuração: chunk_size={chunk_size:,}, bootstrap_samples={bootstrap_samples}, max_columns_per_batch={max_columns_per_batch}")
    
    # Inicialização das estruturas
    sample_dir = os.path.join(DAMICORE_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    
    # Para arquivos pequenos, usa processamento normal consolidado
    if file_size_gb < 5:
        print("📄 Usando processamento consolidado para arquivo pequeno...")
        
        # Carrega o arquivo completo
        df = pd.read_csv(input_path, encoding='utf-8', low_memory=False)
        print(f"Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
        
        # Cria mapeamento de índices para nomes
        from visualization_helper import create_index_to_name_mapping
        index_to_name = create_index_to_name_mapping(df)
        
        # Salva dados consolidados
        consolidated_path = os.path.join(sample_dir, "consolidated_data.csv")
        df.to_csv(consolidated_path, index=False)
        print(f"Dados consolidados salvos: {consolidated_path}")
        
        # === 3. Geração de amostras bootstrap (seguindo lógica original) ===
        print("\n=== GERANDO AMOSTRAS BOOTSTRAP ===")
        for i in range(bootstrap_samples):
            resample_dir = os.path.join(sample_dir, f"resample_{i:02d}")
            os.makedirs(resample_dir, exist_ok=True)
            
            # Reamostragem bootstrap
            resampled_df = df.sample(n=len(df), replace=True, random_state=42+i)
            
            # Salva cada coluna como arquivo de texto separado (formato esperado pelo DAMICORE)
            for col in resampled_df.columns:
                col_path = os.path.join(resample_dir, f"col_{col}.txt")
                resampled_df[col].to_csv(col_path, index=False, header=False, encoding="utf-8")
        
        print(f"Geradas {bootstrap_samples} amostras bootstrap")
        
        # === 4. Execução do DAMICORE para cada amostra (seguindo lógica original) ===
        print("\n=== EXECUTANDO DAMICORE ===")
        damicore_results_dir = os.path.join(DAMICORE_DIR, "damicore_results")
        os.makedirs(damicore_results_dir, exist_ok=True)
        
        import subprocess
        DAMICORE_CLI_PATH = get_damicore_path()
        
        for m in os.listdir(sample_dir):
            resampleddatasource = os.path.join(sample_dir, m)
            if not os.path.isdir(resampleddatasource):
                continue
            
            tree_output = os.path.join(damicore_results_dir, f"{m}-tree.newick")
            argv = [
                "python", DAMICORE_CLI_PATH,
                "--compressor", "gzip",
                "--tree-output", tree_output,
                "--serial",  # Modo serial para evitar problemas de multiprocessing
                resampleddatasource
            ]
            
            print(f"Executando DAMICORE: {' '.join(argv)}")
            process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                print(line, end="")
            process.wait()
            
            if process.returncode != 0:
                print(f"❌ Erro ao executar DAMICORE para {resampleddatasource} (código {process.returncode})")
            else:
                print(f"✅ DAMICORE executado com sucesso para {m}")
        
        # Coleta arquivos newick
        newick_files = []
        for file in os.listdir(damicore_results_dir):
            if file.endswith('.newick'):
                newick_files.append(os.path.join(damicore_results_dir, file))
        
        print(f"Arquivos newick encontrados: {len(newick_files)}")
        
        # Gera visualizações
        if len(newick_files) > 0:
            print("\n=== GERANDO VISUALIZAÇÕES ===")
            from visualization_helper import generate_visualizations
            generate_visualizations(newick_files, DAMICORE_DIR, index_to_name)
        else:
            print("❌ Nenhum arquivo newick encontrado")
        
        return
    
    # Para arquivos grandes, usa processamento streaming com retomada automática
    print("🌊 Usando processamento streaming com retomada automática...")
    
    # Importa o processador streaming com retomada
    from streaming_processor import process_file_streaming
    from resume_processor import get_progress_summary
    
    # Mostra progresso atual (se existir)
    if os.path.exists(DAMICORE_DIR):
        progress_summary = get_progress_summary(DAMICORE_DIR)
        print(f"📊 {progress_summary}")
    else:
        print("📊 Nenhum progresso anterior encontrado - iniciando do zero")
    
    # Configuração V2: processar todas as colunas de uma vez
    max_columns_per_batch = None  # V2: todas as colunas simultaneamente
    
    print(f"🚀 Iniciando processamento com retomada automática...")
    print(f"📊 Configuração V2: chunk_size={chunk_size}, bootstrap={bootstrap_samples}, todas as colunas por chunk")
    
    # Determina o drive externo
    external_drive_path = os.path.dirname(OUTPUT_DIR)
    
    try:
        # Executa processamento com retomada automática
        newick_files = process_file_streaming(
            file_path=input_path,
            chunk_size=chunk_size,
            bootstrap_samples=bootstrap_samples,
            max_columns_per_batch=max_columns_per_batch,
            sample_dir=sample_dir,
            damicore_dir=DAMICORE_DIR,
            external_drive_path=external_drive_path
        )
        
        print(f"✅ Processamento streaming concluído!")
        print(f"🌳 Total de arquivos newick: {len(newick_files)}")
        
        # Gera visualizações se há arquivos newick
        if len(newick_files) > 0:
            print("\n=== GERANDO VISUALIZAÇÕES ===")
            from visualization_helper import generate_visualizations
            
            # Cria mapeamento de índices para nomes (necessário para visualizações)
            print("📋 Criando mapeamento de nomes para visualizações...")
            # Lê apenas o cabeçalho para criar o mapeamento
            df_header = pd.read_csv(input_path, nrows=0)
            from visualization_helper import create_index_to_name_mapping
            index_to_name = create_index_to_name_mapping(df_header)
            
            generate_visualizations(newick_files, DAMICORE_DIR, index_to_name)
        else:
            print("❌ Nenhum arquivo newick encontrado")
            
    except KeyboardInterrupt:
        print("\n⚠️  Processamento interrompido pelo usuário")
        print("🔄 Na próxima execução, o processamento continuará de onde parou!")
        
        if os.path.exists(DAMICORE_DIR):
            progress_summary = get_progress_summary(DAMICORE_DIR)
            print(f"📊 {progress_summary}")
    
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
        print("🔄 Na próxima execução, o processamento continuará de onde parou!")
    print("Use o script original para arquivos grandes")

def main_non_interactive(csv_file):
    """
    Versão não-interativa do main() para execução automatizada.
    """
    print("🚀 DAMICORE + Pareto Analysis (Modo Não-Interativo)")
    print("=" * 50)
    
    # Configurar drive externo automaticamente
    EXTERNAL_DRIVE_PATH = "/media/cristiano-xico/sandbox"
    
    if not os.path.exists(EXTERNAL_DRIVE_PATH):
        print(f"❌ Drive externo não encontrado: {EXTERNAL_DRIVE_PATH}")
        return
    
    print(f"✅ Drive externo configurado: {EXTERNAL_DRIVE_PATH}")
    
    # Verificar espaço livre
    free_space_gb = (os.statvfs(EXTERNAL_DRIVE_PATH).f_frsize * os.statvfs(EXTERNAL_DRIVE_PATH).f_bavail) / (1024**3)
    print(f"📊 Espaço livre no drive externo: {free_space_gb:.1f} GB")
    
    # Verificar arquivo CSV
    if not os.path.exists(csv_file):
        print(f"❌ Erro: Arquivo {csv_file} não encontrado")
        return
    
    file_size_gb = os.path.getsize(csv_file) / (1024**3)
    print(f"📁 Tamanho do arquivo: {file_size_gb:.1f} GB")
    
    # Executar processamento (adaptado da função main original)
    try:
        # Configuração dos diretórios de saída no drive externo
        SCRIPTS_OUTPUT_BASE = os.path.splitext(os.path.basename(csv_file))[0]
        OUTPUT_DIR = os.path.join(EXTERNAL_DRIVE_PATH, "DAMICORE_RESULTS", SCRIPTS_OUTPUT_BASE)
        DAMICORE_DIR = os.path.join(OUTPUT_DIR, "damicore_analysis")
        os.makedirs(DAMICORE_DIR, exist_ok=True)
        
        print(f"📂 Resultados serão salvos em: {OUTPUT_DIR}")
        
        # Executar processamento em chunks
        execute_chunk_processing(csv_file, file_size_gb, OUTPUT_DIR, DAMICORE_DIR)
        
        print("✅ Processamento concluído com sucesso!")
    except Exception as e:
        print(f"❌ Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Modo não-interativo com arquivo fornecido como argumento
        csv_file = sys.argv[1]
        main_non_interactive(csv_file)
    else:
        # Modo interativo original
        main()
