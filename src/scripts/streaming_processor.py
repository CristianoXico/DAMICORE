"""
Processador de streaming para arquivos ultra-grandes
Processa 1 chunk por vez sem acumular na memória
Com suporte a retomada automática
"""

import csv
import random
import sys
import os
import subprocess
import gc
from resume_processor import get_resume_point, update_progress, mark_pipeline_completed

# Aumenta o limite de campo do CSV para lidar com arquivos muito grandes
csv.field_size_limit(sys.maxsize)

def process_file_streaming(file_path, chunk_size, bootstrap_samples, max_columns_per_batch, 
                          sample_dir, damicore_dir, external_drive_path):
    """
    Processa arquivo CSV muito grande em modo streaming com retomada automática
    - Lê 1 chunk por vez
    - Processa imediatamente
    - Executa DAMICORE
    - Libera memória
    - Não acumula chunks na memória
    - Retoma automaticamente de onde parou
    """
    print(f"🌊 MODO STREAMING: Processando {file_path}")
    print(f"📊 Configuração: chunk_size={chunk_size}, bootstrap={bootstrap_samples}")
    
    # Primeiro, conta o total de chunks para determinar ponto de retomada
    total_chunks = 0
    with open(file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Pula cabeçalho
        
        chunk_count = 0
        for row in csv_reader:
            chunk_count += 1
            if chunk_count >= chunk_size:
                total_chunks += 1
                chunk_count = 0
        
        # Último chunk parcial
        if chunk_count > 0:
            total_chunks += 1
    
    print(f"📊 Total estimado de chunks: {total_chunks}")
    
    # Verifica ponto de retomada
    resume_chunk, pending_work = get_resume_point(damicore_dir, total_chunks, bootstrap_samples)
    
    if resume_chunk is None:
        print("✅ Pipeline já completado!")
        # Coleta arquivos newick existentes
        results_dir = os.path.join(damicore_dir, "damicore_results")
        if os.path.exists(results_dir):
            newick_files = [os.path.join(results_dir, f) for f in os.listdir(results_dir) 
                           if f.endswith("-tree.newick")]
        mark_pipeline_completed(damicore_dir)
        return newick_files
    
    headers = None
    chunk_idx = 0
    total_lines = 0
    newick_files = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        
        # Lê cabeçalho
        headers = next(csv_reader)
        print(f"📋 Cabeçalho: {len(headers)} colunas")
        
        current_chunk = []
        
        for row_num, row in enumerate(csv_reader):
            # Garante que a linha tenha o mesmo número de colunas do cabeçalho
            if len(row) != len(headers):
                row = row + [''] * (len(headers) - len(row))
                row = row[:len(headers)]
            
            current_chunk.append(row)
            total_lines += 1
            
            # Quando o chunk está cheio, processa IMEDIATAMENTE
            if len(current_chunk) >= chunk_size:
                
                # Verifica se este chunk precisa ser processado
                chunk_newick_files = []
                if chunk_idx in pending_work:
                    pending_samples = pending_work[chunk_idx]
                    print(f"🔄 Processando chunk {chunk_idx} ({len(current_chunk)} linhas) - Amostras pendentes: {pending_samples}")
                    
                    # Processa apenas as amostras pendentes
                    chunk_newick_files = process_single_chunk_streaming_resume(
                        current_chunk, headers, chunk_idx, bootstrap_samples,
                        max_columns_per_batch, sample_dir, damicore_dir, pending_samples
                    )
                    
                    # Adiciona arquivos newick gerados
                    newick_files.extend(chunk_newick_files)
                else:
                    print(f"⏭️  Pulando chunk {chunk_idx} (já processado completamente)")
                
                # LIBERA MEMÓRIA IMEDIATAMENTE
                current_chunk = []
                del chunk_newick_files
                gc.collect()
                
                chunk_idx += 1
                
                # Mostra progresso
                print(f"✅ Chunk {chunk_idx-1} processado. Total de linhas: {total_lines}")
                
                # Verifica espaço livre periodicamente
                if chunk_idx % 5 == 0:
                    free_space = (os.statvfs(external_drive_path).f_frsize * 
                                os.statvfs(external_drive_path).f_bavail) / (1024**3)
                    print(f"💾 Espaço livre: {free_space:.1f} GB")
                
                # Limpeza agressiva a cada 10 chunks
                if chunk_idx % 10 == 0:
                    print(f"🧹 Limpeza agressiva após {chunk_idx} chunks...")
                    gc.collect()
        
        # Processa último chunk se houver dados restantes
        if current_chunk:
            # Verifica se este último chunk precisa ser processado
            if chunk_idx in pending_work:
                pending_samples = pending_work[chunk_idx]
                print(f"🔄 Processando último chunk {chunk_idx} ({len(current_chunk)} linhas) - Amostras pendentes: {pending_samples}")
                
                # Processa apenas as amostras pendentes
                chunk_newick_files = process_single_chunk_streaming_resume(
                    current_chunk, headers, chunk_idx, bootstrap_samples,
                    max_columns_per_batch, sample_dir, damicore_dir, pending_samples
                )
                newick_files.extend(chunk_newick_files)
            else:
                print(f"⏭️  Pulando último chunk {chunk_idx} (já processado completamente)")
            
            chunk_idx += 1
    
    print(f"🎉 Processamento streaming concluído!")
    print(f"📊 Total: {total_lines} linhas em {chunk_idx} chunks")
    print(f"🌳 Arquivos newick gerados: {len(newick_files)}")
    
    # Marca pipeline como completado
    mark_pipeline_completed(damicore_dir)
    
    return newick_files

def process_single_chunk_streaming(chunk_data, headers, chunk_idx, bootstrap_samples,
                                 max_columns_per_batch, sample_dir, damicore_dir):
    """
    Processa um único chunk em modo streaming
    """
    newick_files = []
    
    # Converte chunk para formato de dicionário
    chunk_dict = {}
    for i, header in enumerate(headers):
        chunk_dict[str(i)] = [row[i] if i < len(row) else '' for row in chunk_data]
    
    # Cria objeto mock DataFrame
    class StreamingDataFrame:
        def __init__(self, data):
            self.data = data
            self.columns = list(data.keys())
            self.shape = (len(chunk_data), len(headers))
        
        def __getitem__(self, key):
            return self.data[key]
        
        def sample(self, n, replace=True, random_state=None):
            if random_state is not None:
                random.seed(random_state)
            
            indices = [random.randint(0, len(self.data[self.columns[0]])-1) for _ in range(n)]
            sampled_data = {}
            for col in self.columns:
                sampled_data[col] = [self.data[col][i] for i in indices]
            
            return StreamingDataFrame(sampled_data)
        
        def copy(self):
            return StreamingDataFrame(self.data.copy())
        
        def map(self, func):
            new_data = {}
            for col in self.columns:
                new_data[col] = [func(val) for val in self.data[col]]
            return StreamingDataFrame(new_data)
    
    # Cria DataFrame mock
    chunk_df = StreamingDataFrame(chunk_dict)
    
    # Aplica limpeza de caracteres
    chunk_df = chunk_df.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)
    
    # Bootstrap com configuração reduzida
    resampled_chunks = [chunk_df.copy()]
    for i in range(bootstrap_samples):
        bootstrap_sample = chunk_df.sample(n=chunk_df.shape[0], replace=True, random_state=i)
        resampled_chunks.append(bootstrap_sample)
    
    # Libera chunk original
    del chunk_df
    gc.collect()
    
    # Processa cada amostra
    for idx, resampled_df in enumerate(resampled_chunks):
        resample_dir = os.path.join(sample_dir, f"chunk_{chunk_idx}_resample_{idx:02d}")
        os.makedirs(resample_dir, exist_ok=True)
        
        # ABORDAGEM V2: Processar todas as colunas de uma vez ou em lotes
        columns = list(resampled_df.columns)
        
        if max_columns_per_batch is None:
            # V2: Processar TODAS as colunas de uma vez
            print(f"    📝 Salvando TODAS as {len(columns)} colunas de uma vez (V2)...")
            for col in columns:
                col_path = os.path.join(resample_dir, f"col_{col}.txt")
                with open(col_path, 'w', encoding='utf-8') as f:
                    for value in resampled_df[col]:
                        f.write(f"{value}\n")
        else:
            # V1: Processar colunas em lotes (fallback)
            print(f"    📝 Salvando {len(columns)} colunas em lotes de {max_columns_per_batch}...")
            for i in range(0, len(columns), max_columns_per_batch):
                col_batch = columns[i:i+max_columns_per_batch]
                
                for col in col_batch:
                    col_path = os.path.join(resample_dir, f"col_{col}.txt")
                    with open(col_path, 'w', encoding='utf-8') as f:
                        for value in resampled_df[col]:
                            f.write(f"{value}\n")
                
                # Limpeza após cada lote
                gc.collect()
        
        print(f"    ✅ Chunk {chunk_idx}, amostra {idx}: {len(columns)} colunas salvas")
        
        # Executa DAMICORE imediatamente
        tree_output_path = os.path.join(damicore_dir, "damicore_results", 
                                      f"chunk_{chunk_idx}_resample_{idx:02d}-tree.newick")
        os.makedirs(os.path.dirname(tree_output_path), exist_ok=True)
        
        cmd = [
            "python", "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/DAMICORE/damicore_py3/damicore.py",
            "--compressor", "gzip",
            "--serial",
            "--tree-output", tree_output_path,
            resample_dir
        ]
        
        print(f"    🔄 Executando DAMICORE para chunk {chunk_idx}, amostra {idx}...")
        try:
            # Timeout aumentado para 2 horas (7200s) para suportar arquivos muito grandes
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=7200)
            print(f"    ✅ DAMICORE executado com sucesso!")
            newick_files.append(tree_output_path)
        except subprocess.TimeoutExpired:
            print(f"    ⚠️  DAMICORE timeout (2h) para chunk {chunk_idx}, amostra {idx}")
        except subprocess.CalledProcessError as e:
            print(f"    ❌ Erro ao executar DAMICORE: {e}")
        
        # Limpeza após DAMICORE
        gc.collect()
    
    # Libera todas as amostras
    for df in resampled_chunks:
        del df
    del resampled_chunks
    gc.collect()
    
    return newick_files


def process_single_chunk_streaming_resume(chunk_data, headers, chunk_idx, bootstrap_samples,
                                         max_columns_per_batch, sample_dir, damicore_dir, pending_samples):
    """
    Processa um único chunk em modo streaming - APENAS amostras pendentes (retomada automática)
    """
    newick_files = []
    
    # Converte chunk para formato de dicionário
    chunk_dict = {}
    for i, header in enumerate(headers):
        chunk_dict[str(i)] = [row[i] if i < len(row) else '' for row in chunk_data]
    
    # Cria objeto mock DataFrame
    class StreamingDataFrame:
        def __init__(self, data):
            self.data = data
            self.columns = list(data.keys())
            self.shape = (len(chunk_data), len(headers))
        
        def __getitem__(self, key):
            return self.data[key]
        
        def sample(self, n, replace=True, random_state=None):
            if random_state is not None:
                random.seed(random_state)
            
            indices = [random.randint(0, len(self.data[self.columns[0]])-1) for _ in range(n)]
            sampled_data = {}
            for col in self.columns:
                sampled_data[col] = [self.data[col][i] for i in indices]
            
            return StreamingDataFrame(sampled_data)
        
        def copy(self):
            return StreamingDataFrame(self.data.copy())
        
        def map(self, func):
            new_data = {}
            for col in self.columns:
                new_data[col] = [func(val) for val in self.data[col]]
            return StreamingDataFrame(new_data)
    
    # Cria DataFrame mock
    chunk_df = StreamingDataFrame(chunk_dict)
    
    # Aplica limpeza de caracteres
    chunk_df = chunk_df.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)
    
    # Processa APENAS as amostras pendentes
    for idx in pending_samples:
        print(f"    🔄 Processando amostra pendente {idx} do chunk {chunk_idx}...")
        
        if idx == 0:
            # Amostra 0 é o chunk original
            resampled_df = chunk_df.copy()
        else:
            # Amostras bootstrap
            resampled_df = chunk_df.sample(n=chunk_df.shape[0], replace=True, random_state=idx-1)
        
        resample_dir = os.path.join(sample_dir, f"chunk_{chunk_idx}_resample_{idx:02d}")
        os.makedirs(resample_dir, exist_ok=True)
        
        # ABORDAGEM V2: Processar todas as colunas de uma vez ou em lotes
        columns = list(resampled_df.columns)
        
        if max_columns_per_batch is None:
            # V2: Processar TODAS as colunas de uma vez
            print(f"      📝 Salvando TODAS as {len(columns)} colunas de uma vez (V2)...")
            for col in columns:
                col_path = os.path.join(resample_dir, f"col_{col}.txt")
                with open(col_path, 'w', encoding='utf-8') as f:
                    for value in resampled_df[col]:
                        f.write(f"{value}\n")
        else:
            # V1: Processar colunas em lotes (fallback)
            print(f"      📝 Salvando {len(columns)} colunas em lotes de {max_columns_per_batch}...")
            for i in range(0, len(columns), max_columns_per_batch):
                col_batch = columns[i:i+max_columns_per_batch]
                
                for col in col_batch:
                    col_path = os.path.join(resample_dir, f"col_{col}.txt")
                    with open(col_path, 'w', encoding='utf-8') as f:
                        for value in resampled_df[col]:
                            f.write(f"{value}\n")
                
                # Limpeza após cada lote
                gc.collect()
        
        print(f"      ✅ Amostra {idx}: {len(columns)} colunas salvas")
        
        # Executa DAMICORE imediatamente
        tree_output_path = os.path.join(damicore_dir, "damicore_results", 
                                      f"chunk_{chunk_idx}_resample_{idx:02d}-tree.newick")
        os.makedirs(os.path.dirname(tree_output_path), exist_ok=True)
        
        cmd = [
            "python", "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/DAMICORE/damicore_py3/damicore.py",
            "--compressor", "gzip",
            "--serial",
            "--tree-output", tree_output_path,
            resample_dir
        ]
        
        print(f"      🔄 Executando DAMICORE para chunk {chunk_idx}, amostra {idx}...")
        try:
            # Timeout aumentado para 2 horas (7200s) para suportar arquivos muito grandes
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=7200)
            print(f"      ✅ DAMICORE executado com sucesso!")
            newick_files.append(tree_output_path)
            
            # Atualiza progresso
            update_progress(damicore_dir, chunk_idx, idx, "completed")
            
        except subprocess.TimeoutExpired:
            print(f"      ⚠️  DAMICORE timeout (2h) para chunk {chunk_idx}, amostra {idx}")
            update_progress(damicore_dir, chunk_idx, idx, "failed")
        except subprocess.CalledProcessError as e:
            print(f"      ❌ Erro ao executar DAMICORE: {e}")
            update_progress(damicore_dir, chunk_idx, idx, "failed")
        
        # Limpeza após DAMICORE
        del resampled_df
        gc.collect()
    
    # Libera chunk original
    del chunk_df
    gc.collect()
    
    return newick_files
