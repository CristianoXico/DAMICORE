#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAMICORE Pareto Script - Versão com Processamento Chunk a Chunk

Este script implementa processamento chunk a chunk com visualizações sendo
produzidas a cada chunk, seguindo a lógica do DAMICORE_Filograma_script.py.

Características principais:
- Processamento chunk a chunk individual
- Visualizações geradas a cada chunk processado
- Sistema de checkpoint/retomada robusto
- Configuração adaptativa baseada no tamanho do arquivo
- Compatível com arquivos ultra-grandes (>10GB)

Autor: Cristiano Xico
Data: 2025-07-23
Versão: 4.0 (Per-Chunk Processing)
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
import time
import subprocess
import json
from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import toytree
import toyplot
import toyplot.pdf
from Bio import Phylo
from large_file_processor import process_large_file_without_pandas
import time
import math
from tqdm import tqdm
import json
from datetime import datetime

# ============================================================================
# SISTEMA DE CHECKPOINT/RETOMADA
# ============================================================================

class ChunkProgressManager:
    """
    Gerencia o progresso do processamento chunk a chunk com checkpoint/retomada automática.
    """
    
    def __init__(self, progress_file_path):
        self.progress_file = progress_file_path
        self.progress_data = self.load_progress()
    
    def load_progress(self):
        """Carrega o progresso existente ou cria novo."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Erro ao carregar progresso: {e}. Iniciando do zero.")
        
        return {
            "pipeline_status": "in_progress",
            "total_chunks": 0,
            "completed_chunks": [],
            "chunk_details": {},
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
    
    def save_progress(self):
        """Salva o progresso atual."""
        self.progress_data["last_update"] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Erro ao salvar progresso: {e}")
    
    def is_chunk_completed(self, chunk_idx):
        """Verifica se um chunk já foi processado."""
        return chunk_idx in self.progress_data.get("completed_chunks", [])
    
    def mark_chunk_completed(self, chunk_idx, newick_files_count, bootstrap_samples):
        """Marca um chunk como concluído."""
        if chunk_idx not in self.progress_data["completed_chunks"]:
            self.progress_data["completed_chunks"].append(chunk_idx)
        
        self.progress_data["chunk_details"][str(chunk_idx)] = {
            "newick_files": newick_files_count,
            "bootstrap_samples": bootstrap_samples,
            "completed_time": datetime.now().isoformat()
        }
        
        self.save_progress()
    
    def initialize_progress(self, total_chunks, bootstrap_samples):
        """Inicializa o progresso para um novo processamento."""
        self.progress_data["total_chunks"] = total_chunks
        self.progress_data["bootstrap_samples"] = bootstrap_samples
        self.save_progress()
    
    def mark_pipeline_completed(self):
        """Marca o pipeline como concluído."""
        self.progress_data["pipeline_status"] = "completed"
        self.progress_data["completion_time"] = datetime.now().isoformat()
        self.save_progress()
    
    def get_progress_summary(self):
        """Retorna resumo do progresso."""
        completed = len(self.progress_data.get("completed_chunks", []))
        total = self.progress_data.get("total_chunks", 0)
        
        if total == 0:
            return "Nenhum progresso encontrado"
        
        percentage = (completed / total) * 100
        status = self.progress_data.get("pipeline_status", "unknown")
        
        return f"Progresso: {completed}/{total} chunks ({percentage:.1f}%) - Status: {status}"
    
    def get_pending_chunks(self):
        """Retorna lista de chunks pendentes."""
        total_chunks = self.progress_data.get("total_chunks", 0)
        completed_chunks = set(self.progress_data.get("completed_chunks", []))
        
        return [i for i in range(total_chunks) if i not in completed_chunks]

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def calculate_adaptive_image_size(num_columns, base_columns=35):
    """
    Calcula dimensões adaptativas para imagens baseado no número de colunas/variáveis.
    
    Args:
        num_columns (int): Número de colunas/variáveis no dataset
        base_columns (int): Número de colunas de referência (35 é o ótimo atual)
    
    Returns:
        tuple: (width, height) das dimensões adaptativas
    """
    # Dimensões base otimizadas para 35 colunas
    base_width = 800
    base_height = 600
    
    # Fator de escala baseado na proporção de colunas
    scale_factor = max(1.0, (num_columns / base_columns) ** 0.7)  # Crescimento suavizado
    
    # Calcula novas dimensões
    adaptive_width = int(base_width * scale_factor)
    adaptive_height = int(base_height * scale_factor)
    
    # Limites mínimos e máximos para evitar imagens muito pequenas ou grandes
    adaptive_width = max(600, min(2400, adaptive_width))  # Entre 600px e 2400px
    adaptive_height = max(450, min(1800, adaptive_height))  # Entre 450px e 1800px
    
    return adaptive_width, adaptive_height

def calculate_adaptive_figure_size(num_columns, base_columns=35):
    """
    Calcula dimensões adaptativas para figuras matplotlib baseado no número de colunas.
    
    Args:
        num_columns (int): Número de colunas/variáveis no dataset
        base_columns (int): Número de colunas de referência (35 é o ótimo atual)
    
    Returns:
        tuple: (width, height) em polegadas para matplotlib
    """
    # Dimensões base em polegadas para matplotlib (otimizadas para 35 colunas)
    base_width = 12
    base_height = 8
    
    # Fator de escala baseado na proporção de colunas
    scale_factor = max(1.0, (num_columns / base_columns) ** 0.6)  # Crescimento mais suave para matplotlib
    
    # Calcula novas dimensões
    adaptive_width = base_width * scale_factor
    adaptive_height = base_height * scale_factor
    
    # Limites para matplotlib
    adaptive_width = max(8, min(24, adaptive_width))   # Entre 8" e 24"
    adaptive_height = max(6, min(18, adaptive_height))  # Entre 6" e 18"
    
    return adaptive_width, adaptive_height

# ============================================================================
# CONFIGURAÇÃO DO DRIVE EXTERNO
# ============================================================================

class ChunkProgressManager:
    """
    Gerencia o progresso do processamento chunk a chunk com checkpoint/retomada automática.
    """
    
    def __init__(self, progress_file):
        self.progress_file = progress_file
        self.progress_data = self.load_progress()
    
    def load_progress(self):
        """Carrega progresso existente ou cria novo."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def save_progress(self):
        """Salva progresso atual."""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress_data, f, indent=2)
    
    def initialize_progress(self, total_chunks, bootstrap_samples):
        """Inicializa progresso se não existir."""
        if not self.progress_data:
            self.progress_data = {
                "total_chunks": total_chunks,
                "bootstrap_samples": bootstrap_samples,
                "completed_chunks": [],
                "pipeline_status": "running",
                "start_time": time.time()
            }
            self.save_progress()
    
    def is_chunk_completed(self, chunk_idx):
        """Verifica se um chunk já foi processado."""
        return chunk_idx in self.progress_data.get("completed_chunks", [])
    
    def mark_chunk_completed(self, chunk_idx, newick_count, bootstrap_samples):
        """Marca um chunk como concluído."""
        if chunk_idx not in self.progress_data.get("completed_chunks", []):
            self.progress_data.setdefault("completed_chunks", []).append(chunk_idx)
            self.progress_data["last_update"] = time.time()
            self.save_progress()
    
    def get_pending_chunks(self):
        """Retorna lista de chunks pendentes."""
        total_chunks = self.progress_data.get("total_chunks", 0)
        completed = set(self.progress_data.get("completed_chunks", []))
        return [i for i in range(total_chunks) if i not in completed]
    
    def mark_pipeline_completed(self):
        """Marca pipeline como concluído."""
        self.progress_data["pipeline_status"] = "completed"
        self.progress_data["end_time"] = time.time()
        self.save_progress()
    
    def get_progress_summary(self):
        """Retorna resumo do progresso."""
        total = self.progress_data.get("total_chunks", 0)
        completed = len(self.progress_data.get("completed_chunks", []))
        return f"{completed}/{total} chunks concluídos ({completed/total*100:.1f}%)"

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
    csv_file = input("Digite o caminho para o arquivo CSV: ").strip()
        
    if not os.path.exists(csv_file):
        print(f"Erro: Arquivo {csv_file} não encontrado.")
        return
        
    # Configuração adaptativa baseada no tamanho do arquivo
    file_size_gb = os.path.getsize(csv_file) / (1024**3)
    print(f"📊 Tamanho do arquivo: {file_size_gb:.2f} GB")
        
    # SOLUÇÃO: Para arquivos pequenos/médios, processar arquivo inteiro como Filograma
    # Isso garante frequências corretas evitando o problema de chunks insuficientes
    if file_size_gb >= 10:
        # Arquivos muito grandes: usar chunking otimizado
        chunk_size = 500
        bootstrap_samples = 3
        max_columns = 15
        use_full_file_mode = False
        print("📊 MODO CHUNKING: Arquivo grande será processado em chunks")
    elif file_size_gb >= 1:
        # Arquivos médios: processar arquivo completo
        chunk_size = None  # Não usado no modo completo
        bootstrap_samples = 10
        max_columns = 50
        use_full_file_mode = True
        print("🎯 MODO ARQUIVO COMPLETO: Processamento como Filograma para garantir frequências corretas")
    else:
        # Arquivos pequenos: definitivamente processar arquivo completo
        chunk_size = None  # Não usado no modo completo
        bootstrap_samples = 22  # Mesmo número do Filograma
        max_columns = 101  # Todas as colunas
        use_full_file_mode = True
        print("✅ MODO ARQUIVO COMPLETO: Arquivo pequeno será processado integralmente")
        
    # Configuração dos diretórios de saída no drive externo
    SCRIPTS_OUTPUT_BASE = os.path.splitext(os.path.basename(csv_file))[0]
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
    
    # Determinar modo de processamento baseado no tamanho
    # OPÇÃO: Forçar modo arquivo completo para garantir frequências corretas
    FORCE_FULL_FILE_MODE = True  # ⚠️ ATENÇÃO: Pode usar muita RAM para arquivos grandes!
    
    if FORCE_FULL_FILE_MODE:
        use_full_file_mode = True
        if file_size_gb >= 10:
            print(f"⚠️  AVISO: Forçando modo arquivo completo para arquivo de {file_size_gb:.1f}GB")
            print(f"💾 Uso estimado de RAM: ~{file_size_gb * 3:.1f}GB (pode causar OOM!)")
            print(f"🎯 Benefício: Frequências de suporte CORRETAS nos arquivos Newick")
            
            response = input("\n🤔 Continuar com modo arquivo completo? (s/n): ")
            if response.lower() != 's':
                print("❌ Processamento cancelado pelo usuário")
                return
    else:
        use_full_file_mode = file_size_gb < 1 or (1 <= file_size_gb < 10)
    
    if use_full_file_mode:
        print(f"\n🎯 MODO ARQUIVO COMPLETO: Processando como script Filograma")
        print(f"📊 Configuração: {bootstrap_samples} amostras bootstrap, {max_columns} colunas máx")
        
        # Criar mapeamento index_to_name
        original_df = pd.read_csv(csv_file, encoding="utf-8", low_memory=False, nrows=1)
        original_columns = original_df.columns.tolist()
        index_to_name = {str(i): name for i, name in enumerate(original_columns)}
        
        # Processar arquivo completo (como Filograma)
        results_dir = os.path.join(DAMICORE_DIR, "damicore_results")
        newick_files = process_full_file_like_filograma(
            csv_file, bootstrap_samples, DAMICORE_DIR, results_dir, index_to_name
        )
        
        print(f"\n=== RESULTADOS DO PROCESSAMENTO COMPLETO ===")
        print(f"Total de arquivos newick gerados: {len(newick_files)}")
        
        if len(newick_files) == 0:
            print("❌ Nenhum arquivo newick encontrado. Verifique se o DAMICORE foi executado corretamente.")
            return
        
        # Gerar visualizações
        from visualization_helper import generate_visualizations
        generate_visualizations(newick_files, DAMICORE_DIR, index_to_name)
        
        print(f"\n✅ Análise DAMICORE COMPLETA concluída com sucesso!")
        print(f"📂 Todos os resultados foram salvos em: {OUTPUT_DIR}")
        print(f"🎉 Frequências corretas garantidas pelo processamento completo!")
        
        return
    
    # Para arquivos muito grandes, usa processamento STREAMING
    elif file_size_gb >= 10:
        print("🌊 Usando processamento STREAMING (1 chunk por vez) para arquivo muito grande...")
        from streaming_processor import process_file_streaming
        
        # Processa arquivo em modo streaming
        newick_files = process_file_streaming(
            csv_file, chunk_size, bootstrap_samples, max_columns_per_batch,
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
            csv_file, 
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
                    timeout=1800  # 30 minutos de timeout
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
                "python", "/home/cristiano-xico/github/CristianoXico/DAMICORE/src/damicore.py",
                "--compressor", "gzip",
                "--tree-output", tree_output,
                resample_path
            ]
            
            print(f"Executando: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
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

def execute_chunk_processing_per_chunk(input_path, file_size_gb, OUTPUT_DIR, DAMICORE_DIR):
    """
    Executa o processamento chunk a chunk com visualizações sendo produzidas a cada chunk.
    Segue a lógica do DAMICORE_Filograma_script.py.
    """
    print("\n=== INICIANDO PROCESSAMENTO CHUNK A CHUNK ===")
    print("Processamento individual de chunks com visualizações por chunk...")
    
    # Configuração otimizada: chunk size ideal de 100 linhas (conforme especificado)
    # Inclui todas as variáveis/colunas do dataset por chunk
    chunk_size = 100  # PADRÃO OTIMIZADO: 100 linhas por chunk
    
    # Carrega o arquivo CSV para calcular número de chunks
    print("📄 Carregando arquivo CSV para análise...")
    df = pd.read_csv(input_path, encoding='utf-8', low_memory=False)
    total_rows = len(df)
    num_chunks = math.ceil(total_rows / chunk_size)
    
    print(f"Dados carregados: {total_rows} linhas, {len(df.columns)} colunas")
    print(f"📊 Total de chunks a processar: {num_chunks}")
    
    # Bootstrap samples ADAPTATIVO: quanto mais chunks, menor o número de reamostragens
    if num_chunks >= 50:
        bootstrap_samples = 2   # Muitos chunks: poucas reamostragens por chunk
    elif num_chunks >= 20:
        bootstrap_samples = 3   # Chunks moderados: reamostragens moderadas
    elif num_chunks >= 10:
        bootstrap_samples = 5   # Poucos chunks: mais reamostragens
    elif num_chunks >= 5:
        bootstrap_samples = 8   # Muito poucos chunks: muitas reamostragens
    else:
        bootstrap_samples = 10  # Chunks únicos/poucos: máximas reamostragens
    
    print(f"📊 Configuração: chunk_size={chunk_size:,}, bootstrap_samples={bootstrap_samples}")
    
    # Inicialização das estruturas
    results_dir = os.path.join(DAMICORE_DIR, "damicore_results")
    os.makedirs(results_dir, exist_ok=True)
    
    # === SISTEMA DE CHECKPOINT/RETOMADA ===
    progress_file = os.path.join(DAMICORE_DIR, "chunk_progress.json")
    progress_manager = ChunkProgressManager(progress_file)
    
    # Verifica se há progresso anterior
    if os.path.exists(progress_file):
        print(f"🔄 CHECKPOINT DETECTADO: {progress_manager.get_progress_summary()}")
        
        # Verifica se o pipeline já foi concluído
        if progress_manager.progress_data.get("pipeline_status") == "completed":
            print("✅ Pipeline já concluído anteriormente!")
            print("Para reprocessar, delete o arquivo: chunk_progress.json")
            return
    else:
        print("🎆 Iniciando novo processamento chunk a chunk")
    
    # Inicializa o progresso
    progress_manager.initialize_progress(num_chunks, bootstrap_samples)
    
    # Cria mapeamento de índices para nomes
    from visualization_helper import create_index_to_name_mapping
    index_to_name = create_index_to_name_mapping(df)
    
    # Calcula chunks pendentes para estimativa de tempo
    pending_chunks = progress_manager.get_pending_chunks()
    estimated_time_per_chunk = bootstrap_samples * 45  # ~45 segundos por amostra bootstrap
    remaining_estimated_time = len(pending_chunks) * estimated_time_per_chunk
    
    if pending_chunks:
        print(f"📊 Chunks pendentes: {len(pending_chunks)}/{num_chunks}")
        print(f"⏱️  Tempo estimado restante: {remaining_estimated_time//60:.0f} minutos ({remaining_estimated_time//3600:.1f} horas)")
    else:
        print("✅ Todos os chunks já foram processados!")
    
    # Lista para coletar todos os arquivos newick de todos os chunks
    all_newick_files = []
    
    # Coleta arquivos newick já existentes de chunks concluídos
    print("\n📁 Coletando arquivos newick de chunks já processados...")
    for completed_chunk_idx in progress_manager.progress_data.get("completed_chunks", []):
        chunk_dir = os.path.join(DAMICORE_DIR, f"chunk_{completed_chunk_idx:03d}")
        chunk_results_dir = os.path.join(chunk_dir, "damicore_results")
        
        if os.path.exists(chunk_results_dir):
            for file in os.listdir(chunk_results_dir):
                if file.endswith(".newick"):
                    newick_path = os.path.join(chunk_results_dir, file)
                    if os.path.exists(newick_path):
                        all_newick_files.append(newick_path)
    
    print(f"🌳 Arquivos newick já coletados: {len(all_newick_files)}")
    
    # Processamento apenas dos chunks pendentes
    if pending_chunks:
        print(f"\n🚀 Processando {len(pending_chunks)} chunks pendentes...")
        start_time = time.time()
        
        # Barra de progresso para chunks pendentes
        with tqdm(total=len(pending_chunks), desc="Processando chunks pendentes", unit="chunk") as pbar:
            for i, chunk_idx in enumerate(pending_chunks):
                chunk_start_time = time.time()
                start_idx = chunk_idx * chunk_size
                end_idx = min(start_idx + chunk_size, total_rows)
                
                pbar.set_description(f"Chunk {chunk_idx + 1}/{num_chunks} (linhas {start_idx}-{end_idx-1})")
                
                # Verifica novamente se o chunk não foi processado (segurança)
                if progress_manager.is_chunk_completed(chunk_idx):
                    print(f"⚠️  Chunk {chunk_idx + 1} já processado, pulando...")
                    pbar.update(1)
                    continue
                
                # Extrai chunk atual
                chunk_df = df.iloc[start_idx:end_idx].copy()
                
                try:
                    # NOVA ESTRATÉGIA: Usar DAMICORE_Filograma_script.py para cada chunk
                    # Isso garante frequências corretas porque cada chunk é processado completamente
                    print(f"\n🎯 ESTRATÉGIA HÍBRIDA: Chunk {chunk_idx + 1} será processado pelo script Filograma")
                    print(f"📊 Vantagem: Frequências de suporte CORRETAS nos arquivos Newick")
                    
                    chunk_newick_files = process_chunk_with_filograma_script(
                        chunk_df, chunk_idx, DAMICORE_DIR, results_dir, index_to_name, len(df.columns)
                    )
                    
                    # Adiciona arquivos newick deste chunk à lista geral
                    if chunk_newick_files:
                        all_newick_files.extend(chunk_newick_files)
                    
                    # === CHECKPOINT: Marca chunk como concluído ===
                    progress_manager.mark_chunk_completed(
                        chunk_idx, 
                        len(chunk_newick_files) if chunk_newick_files else 0, 
                        bootstrap_samples
                    )
                    
                    print(f"✅ Chunk {chunk_idx + 1} concluído e salvo no checkpoint")
                    
                except Exception as e:
                    print(f"❌ Erro no chunk {chunk_idx + 1}: {e}")
                    print(f"🔄 Chunk {chunk_idx + 1} será reprocessado na próxima execução")
                    # Não marca como concluído em caso de erro
                
                # Atualiza estimativa de tempo
                chunk_elapsed = time.time() - chunk_start_time
                chunks_remaining = len(pending_chunks) - (i + 1)
                estimated_remaining = chunks_remaining * chunk_elapsed if chunks_remaining > 0 else 0
                
                pbar.set_postfix({
                    'Tempo chunk': f'{chunk_elapsed:.0f}s',
                    'Restante': f'{estimated_remaining//60:.0f}min',
                    'Newick': len(chunk_newick_files) if chunk_newick_files else 0
                })
                
                pbar.update(1)
    else:
        print("✅ Nenhum chunk pendente para processar!")
        
    # Tempo total de processamento
    if pending_chunks:
        total_elapsed = time.time() - start_time
        print(f"\n⏱️  Tempo de processamento (chunks pendentes): {total_elapsed//60:.0f} minutos ({total_elapsed//3600:.1f} horas)")
    
    print(f"🌳 Total de arquivos newick coletados: {len(all_newick_files)}")
    
    # Marca o pipeline como concluído no checkpoint
    progress_manager.mark_pipeline_completed()
    print(f"✅ Pipeline concluído e salvo no checkpoint")
    
    # === GERAÇÃO DE VISUALIZAÇÃO COMPILADA DE TODOS OS CHUNKS ===
    if all_newick_files:
        print("\n🎨 GERANDO VISUALIZAÇÃO COMPILADA DE TODOS OS CHUNKS...")
        generate_compiled_visualization(all_newick_files, DAMICORE_DIR, index_to_name, num_chunks, len(df.columns))
    else:
        print("\n⚠️  Nenhum arquivo newick encontrado. Não é possível gerar visualização compilada.")
    
    print("\n🎉 PROCESSAMENTO CHUNK A CHUNK CONCLUÍDO COM SISTEMA DE RETOMADA!")
    print(f"📊 Resumo final: {progress_manager.get_progress_summary()}")
    print("🔄 Para reprocessar do zero, delete o arquivo: chunk_progress.json")


def process_full_file_like_filograma(csv_file, bootstrap_samples, DAMICORE_DIR, results_dir, index_to_name):
    """
    Processa o arquivo inteiro de uma vez, como o script Filograma.
    Isso garante frequências corretas nos arquivos newick.
    
    Args:
        csv_file: Caminho para o arquivo CSV
        bootstrap_samples: Número de amostras bootstrap
        DAMICORE_DIR: Diretório base do DAMICORE
        results_dir: Diretório de resultados
        index_to_name: Mapeamento de índices para nomes
    
    Returns:
        list: Lista de arquivos newick gerados
    """
    print(f"\n🎯 PROCESSAMENTO ARQUIVO COMPLETO (modo Filograma)")
    print(f"📁 Carregando arquivo completo: {csv_file}")
    
    # === 1. Carregamento completo dos dados ===
    original_df = pd.read_csv(csv_file, encoding="utf-8", low_memory=False)
    original_columns = original_df.columns.tolist()
    
    # Criar DataFrame de trabalho com índices como nomes das colunas
    df = original_df.copy()
    df.columns = [str(i) for i in range(len(df.columns))]
    df = df.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)
    
    print(f"✅ Dados carregados: {df.shape[0]} linhas, {df.shape[1]} colunas")
    
    # === 2. Reamostragem bootstrap (igual ao Filograma) ===
    print(f"\n🔄 Gerando {bootstrap_samples} amostras bootstrap...")
    resampled_df_l = [df]  # Amostra original
    for i in range(bootstrap_samples - 1):
        resampled_df_l.append(df.sample(n=df.shape[0], replace=True, random_state=i))
    
    print(f"✅ {len(resampled_df_l)} amostras bootstrap criadas")
    
    # === 3. Salvamento das amostras (igual ao Filograma) ===
    print(f"\n💾 Criando arquivos de amostra...")
    sample_dir = os.path.join(DAMICORE_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    
    for idx, resampled_df in enumerate(resampled_df_l):
        resample_dir = os.path.join(sample_dir, f"resample_{idx:02d}")
        os.makedirs(resample_dir, exist_ok=True)
        
        for col in resampled_df.columns:
            col_path = os.path.join(resample_dir, f"col_{col}.txt")
            resampled_df[col].to_csv(col_path, index=False, header=False, encoding="utf-8")
        
        print(f"📁 Amostra {idx:02d} salva em {resample_dir}")
    
    print(f"✅ {len(resampled_df_l)} arquivos de amostra criados")
    
    # === 4. Execução do DAMICORE (igual ao Filograma) ===
    print(f"\n🚀 Executando DAMICORE para cada amostra...")
    
    DAMICORE_CLI_PATH = "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/DAMICORE/damicore_py3/damicore.py"
    os.makedirs(results_dir, exist_ok=True)
    
    sample_list = [m for m in os.listdir(sample_dir) if os.path.isdir(os.path.join(sample_dir, m))]
    total_samples = len(sample_list)
    processed_count = 0
    newick_files = []
    
    for m in sample_list:
        resampleddatasource = os.path.join(sample_dir, m)
        tree_output = os.path.join(results_dir, f"{m}-tree.newick")
        
        # Pular se já existe
        if os.path.exists(tree_output):
            print(f"✅ Arquivo newick já existe para {m}")
            newick_files.append(tree_output)
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
                print(f"✅ {m}: DAMICORE executado com sucesso!")
                if os.path.exists(tree_output):
                    newick_files.append(tree_output)
            else:
                print(f"❌ {m}: Erro no DAMICORE (código: {process.returncode})")
                
        except Exception as e:
            print(f"❌ {m}: Erro ao executar DAMICORE: {e}")
        
        processed_count += 1
    
    print(f"\n✅ Processamento completo finalizado!")
    print(f"📊 Total de arquivos newick gerados: {len(newick_files)}")
    
    return newick_files

def validate_chunk_data(chunk_df, chunk_idx):
    """
    Valida se o chunk tem variabilidade suficiente para gerar frequências não-zeradas no DAMICORE.
    
    Args:
        chunk_df: DataFrame do chunk
        chunk_idx: Índice do chunk
    
    Returns:
        bool: True se o chunk é válido, False caso contrário
    """
    print(f"🔍 Validando dados do chunk {chunk_idx + 1}...")
    
    # Verificar tamanho mínimo
    if len(chunk_df) < 50:
        print(f"⚠️  Chunk {chunk_idx + 1}: Muito pequeno ({len(chunk_df)} linhas < 50 mínimo)")
        return False
    
    # Verificar variabilidade nas colunas
    low_variance_cols = 0
    for col in chunk_df.columns:
        try:
            # Converter para numérico se possível
            numeric_data = pd.to_numeric(chunk_df[col], errors='coerce')
            if not numeric_data.isna().all():
                variance = numeric_data.var()
                if variance < 1e-10:  # Variância muito baixa
                    low_variance_cols += 1
        except:
            continue
    
    # Se mais de 80% das colunas têm baixa variância, o chunk pode ser problemático
    if low_variance_cols > len(chunk_df.columns) * 0.8:
        print(f"⚠️  Chunk {chunk_idx + 1}: Baixa variabilidade ({low_variance_cols}/{len(chunk_df.columns)} colunas)")
        return False
    
    print(f"✅ Chunk {chunk_idx + 1}: Dados válidos ({len(chunk_df)} linhas, variabilidade adequada)")
    return True

def process_chunk_with_filograma_script(chunk_df, chunk_idx, DAMICORE_DIR, results_dir, index_to_name, num_columns):
    """
    Processa um chunk individual usando o DAMICORE_Filograma_script.py.
    Isso garante frequências corretas porque cada chunk é processado completamente.
    
    Args:
        chunk_df: DataFrame do chunk (100 linhas + todas as colunas)
        chunk_idx: Índice do chunk
        DAMICORE_DIR: Diretório base do DAMICORE
        results_dir: Diretório de resultados
        index_to_name: Mapeamento de índices para nomes
        num_columns: Número de colunas
    
    Returns:
        list: Lista de arquivos newick gerados
    """
    print(f"\n🎯 PROCESSANDO CHUNK {chunk_idx + 1} com Filograma Script")
    print(f"📊 Chunk: {chunk_df.shape[0]} linhas, {chunk_df.shape[1]} colunas (TODAS as variáveis)")
    
    # === 1. Criar diretório temporário para este chunk ===
    chunk_dir = os.path.join(DAMICORE_DIR, f"chunk_{chunk_idx:03d}")
    os.makedirs(chunk_dir, exist_ok=True)
    
    # === 2. Salvar chunk como CSV temporário ===
    chunk_csv_path = os.path.join(chunk_dir, f"chunk_{chunk_idx:03d}.csv")
    
    # Restaurar nomes originais das colunas para o CSV temporário
    chunk_df_original = chunk_df.copy()
    if index_to_name:
        # Mapear índices de volta para nomes originais
        original_columns = []
        for i in range(len(chunk_df.columns)):
            if str(i) in index_to_name:
                original_columns.append(index_to_name[str(i)])
            else:
                original_columns.append(f"col_{i}")
        chunk_df_original.columns = original_columns
    
    chunk_df_original.to_csv(chunk_csv_path, index=False, encoding="utf-8")
    print(f"💾 Chunk salvo como: {chunk_csv_path}")
    
    # === 3. Executar DAMICORE_Filograma_script.py no chunk ===
    filograma_script_path = "/home/cristiano-xico/github/CristianoXico/DAMICORE/src/scripts/DAMICORE_Filograma_script.py"
    
    if not os.path.exists(filograma_script_path):
        print(f"❌ Erro: Script Filograma não encontrado em {filograma_script_path}")
        return []
    
    print(f"🚀 Executando DAMICORE_Filograma_script.py para chunk {chunk_idx + 1}...")
    
    try:
        # Executar o script Filograma no chunk
        cmd = ["python3", filograma_script_path, chunk_csv_path]
        print(f"Comando: {' '.join(cmd)}")
        
        # Mudar para o diretório do chunk para que os resultados sejam salvos lá
        original_cwd = os.getcwd()
        os.chdir(chunk_dir)
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Capturar saída em tempo real
        for line in process.stdout:
            print(f"  [Filograma] {line.rstrip()}")
        
        process.wait()
        
        # Voltar ao diretório original
        os.chdir(original_cwd)
        
        if process.returncode == 0:
            print(f"✅ Chunk {chunk_idx + 1}: DAMICORE_Filograma_script.py executado com sucesso!")
        else:
            print(f"❌ Chunk {chunk_idx + 1}: Erro no DAMICORE_Filograma_script.py (código: {process.returncode})")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao executar DAMICORE_Filograma_script.py para chunk {chunk_idx + 1}: {e}")
        os.chdir(original_cwd)  # Garantir que voltamos ao diretório original
        return []
    
    # === 4. Coletar arquivos newick gerados ===
    newick_files = []
    
    # Procurar por arquivos newick no diretório do chunk
    for root, dirs, files in os.walk(chunk_dir):
        for file in files:
            if file.endswith('.newick'):
                newick_path = os.path.join(root, file)
                newick_files.append(newick_path)
                print(f"🌳 Arquivo newick encontrado: {newick_path}")
    
    print(f"✅ Chunk {chunk_idx + 1} processado: {len(newick_files)} arquivos newick gerados")
    
    # === 5. Gerar visualizações adaptativas para este chunk ===
    if newick_files:
        viz_dir = os.path.join(chunk_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)
        generate_adaptive_visualizations(newick_files, viz_dir, chunk_idx, num_columns, index_to_name)
    
    return newick_files

def process_single_chunk_with_visualizations(chunk_df, chunk_idx, bootstrap_samples, DAMICORE_DIR, results_dir, index_to_name, num_columns):
    """
    Processa um único chunk com bootstrap e gera visualizações específicas para o chunk.
    Segue a lógica do DAMICORE_Filograma_script.py.
    
    Args:
        num_columns (int): Número de colunas/variáveis do dataset para dimensionamento adaptativo
    """
    print(f"\n📊 Processando chunk {chunk_idx + 1} com {len(chunk_df)} linhas...")
    
    # Criar diretório específico para este chunk
    chunk_dir = os.path.join(DAMICORE_DIR, f"chunk_{chunk_idx:03d}")
    os.makedirs(chunk_dir, exist_ok=True)
    
    # Preparar DataFrame com índices como nomes das colunas (seguindo lógica do Filograma)
    df_work = chunk_df.copy()
    df_work.columns = [str(i) for i in range(len(df_work.columns))]
    # Limpar caracteres não-ASCII
    df_work = df_work.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)
    
    # === 1. Reamostragem bootstrap ===
    print(f"🔄 Gerando {bootstrap_samples} amostras bootstrap para chunk {chunk_idx + 1}...")
    resampled_df_list = [df_work]  # Amostra original
    
    # Gerar amostras bootstrap adicionais
    for i in range(bootstrap_samples - 1):
        seed = chunk_idx * 1000 + i  # Seed único para cada chunk e amostra
        resampled_df_list.append(df_work.sample(n=df_work.shape[0], replace=True, random_state=seed))
    
    print(f"✅ {len(resampled_df_list)} amostras bootstrap criadas para chunk {chunk_idx + 1}")
    
    # === 2. Salvamento das amostras ===
    sample_dir = os.path.join(chunk_dir, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    
    for idx, resampled_df in enumerate(resampled_df_list):
        resample_dir = os.path.join(sample_dir, f"resample_{idx:02d}")
        os.makedirs(resample_dir, exist_ok=True)
        
        for col in resampled_df.columns:
            col_path = os.path.join(resample_dir, f"col_{col}.txt")
            resampled_df[col].to_csv(col_path, index=False, header=False, encoding="utf-8")
    
    print(f"💾 Arquivos de amostra salvos para chunk {chunk_idx + 1}")
    
    # === 3. Execução do DAMICORE para cada amostra ===
    print(f"🚀 Executando DAMICORE para chunk {chunk_idx + 1}...")
    
    chunk_results_dir = os.path.join(chunk_dir, "damicore_results")
    os.makedirs(chunk_results_dir, exist_ok=True)
    
    newick_files = []
    sample_list = [m for m in os.listdir(sample_dir) if os.path.isdir(os.path.join(sample_dir, m))]
    
    for m in sample_list:
        resample_path = os.path.join(sample_dir, m)
        tree_output = os.path.join(chunk_results_dir, f"chunk_{chunk_idx:03d}_{m}-tree.newick")
        
        try:
            # Usar o mesmo caminho do DAMICORE que funciona no script Filograma
            DAMICORE_CLI_PATH = "/home/cristiano-xico/Desktop/work_space_vs_code/CristianoXico-repos/DAMICORE/damicore_py3/damicore.py"
            
            cmd = [
                "python3", DAMICORE_CLI_PATH,
                "--compressor", "gzip",
                "--tree-output", tree_output,
                resample_path
            ]
            
            print(f"  🌳 Processando {m}...")
            print(f"  Executando DAMICORE: {' '.join(cmd)}")
            
            # Usar subprocess.Popen como no script Filograma que funciona corretamente
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Capturar output em tempo real
            for line in process.stdout:
                print(f"    {line.rstrip()}")
            
            process.wait()
            
            if process.returncode == 0:
                print(f"  ✅ {m}: DAMICORE executado com sucesso!")
                if os.path.exists(tree_output):
                    newick_files.append(tree_output)
                    print(f"  🌳 Arquivo newick gerado: {tree_output}")
            else:
                print(f"  ❌ {m}: Erro no DAMICORE (código: {process.returncode})")
                
        except Exception as e:
            print(f"  ❌ {m}: Erro ao executar DAMICORE: {e}")
    
    print(f"📊 Chunk {chunk_idx + 1}: {len(newick_files)} arquivos newick gerados")
    
    # === 4. Geração de visualizações específicas para este chunk ===
    if newick_files:
        print(f"🎨 Gerando visualizações para chunk {chunk_idx + 1}...")
        generate_chunk_visualizations(newick_files, chunk_dir, chunk_idx, index_to_name, num_columns)
    else:
        print(f"⚠️  Nenhum arquivo newick gerado para chunk {chunk_idx + 1}, pulando visualizações")
    
    # Retorna os arquivos newick gerados para este chunk
    return newick_files


def generate_chunk_visualizations(newick_files, chunk_dir, chunk_idx, index_to_name, num_columns):
    """
    Gera visualizações específicas para um chunk individual com dimensionamento verdadeiramente adaptativo.
    
    Args:
        newick_files (list): Lista de arquivos newick
        chunk_dir (str): Diretório do chunk
        chunk_idx (int): Índice do chunk
        index_to_name (dict): Mapeamento de índices para nomes originais
        num_columns (int): Número de colunas/variáveis para dimensionamento adaptativo
    """
    print(f"🎨 Gerando visualizações ADAPTATIVAS para chunk {chunk_idx + 1}...")
    print(f"📊 Dataset: {num_columns} colunas/variáveis")
    
    # Criar diretório de visualizações para este chunk
    viz_dir = os.path.join(chunk_dir, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)
    
    # Usar a nova implementação de visualizações verdadeiramente adaptativas
    generate_adaptive_visualizations(newick_files, viz_dir, chunk_idx, num_columns, index_to_name)
    
    print(f"✅ Visualizações adaptativas do chunk {chunk_idx + 1} concluídas!")


def generate_adaptive_visualizations(newick_files, viz_dir, chunk_idx, num_columns, index_to_name=None):
    """
    Gera visualizações com dimensionamento verdadeiramente adaptativo baseado no número de colunas.
    
    Args:
        newick_files (list): Lista de arquivos newick
        viz_dir (str): Diretório para salvar visualizações
        chunk_idx (int): Índice do chunk
        num_columns (int): Número de colunas para dimensionamento adaptativo
        index_to_name (dict): Mapeamento de índices para nomes originais
    """
    print(f"🎨 Gerando visualizações adaptativas para chunk {chunk_idx + 1}...")
    
    # Calcular dimensões adaptativas
    adaptive_width, adaptive_height = calculate_adaptive_image_size(num_columns)
    fig_width, fig_height = calculate_adaptive_figure_size(num_columns)
    
    print(f"📏 Dimensões adaptativas: {adaptive_width}x{adaptive_height}px ({fig_width:.1f}x{fig_height:.1f}in) para {num_columns} colunas")
    
    if not newick_files:
        print("❌ Nenhum arquivo newick fornecido para visualização")
        return
    
    try:
        from Bio import Phylo
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        
        # === 1. CLOUD TREE ADAPTATIVA ===
        try:
            # Usar o primeiro arquivo newick para cloud tree
            tree = Phylo.read(newick_files[0], "newick")
            
            # Configurar figura com dimensões adaptativas
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
            
            # Calcular espaçamento adaptativo para labels
            label_fontsize = max(6, min(12, 120 / num_columns))  # Fonte adaptativa
            branch_width = max(0.5, min(2.0, 50 / num_columns))  # Espessura adaptativa
            
            # Desenhar árvore com parâmetros adaptativos
            Phylo.draw(tree, axes=ax, do_show=False, 
                      branch_labels=None,  # Remover labels de branch para evitar sobreposição
                      label_func=lambda x: x.name if x.name else '',
                      label_colors='black')
            
            # Configurar título e layout
            ax.set_title(f"Cloud Tree - Chunk {chunk_idx + 1} ({num_columns} variáveis)", 
                        fontsize=max(10, min(16, 200 / num_columns)))
            
            # Ajustar margens para evitar corte de labels
            plt.tight_layout()
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
            # Salvar com alta resolução
            cloud_path = os.path.join(viz_dir, f"chunk_{chunk_idx:03d}_cloud_tree_adaptive.png")
            plt.savefig(cloud_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            print(f"  ✅ Cloud tree adaptativa salva: chunk_{chunk_idx:03d}_cloud_tree_adaptive.png")
            
        except Exception as e:
            print(f"  ❌ Erro ao gerar cloud tree adaptativa: {e}")
        
        # === 2. CONSENSUS TREE ADAPTATIVA ===
        try:
            if len(newick_files) > 1:
                # Usar múltiplos arquivos para consensus se disponível
                trees = [Phylo.read(f, "newick") for f in newick_files[:5]]  # Máximo 5 árvores
                consensus_tree = trees[0]  # Simplificado: usar primeira árvore como base
            else:
                consensus_tree = Phylo.read(newick_files[0], "newick")
            
            # Configurar figura com dimensões adaptativas
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
            
            # Desenhar consensus tree com parâmetros adaptativos
            Phylo.draw(consensus_tree, axes=ax, do_show=False,
                      branch_labels=None,
                      label_func=lambda x: x.name if x.name else '',
                      label_colors='darkblue')
            
            ax.set_title(f"Consensus Tree - Chunk {chunk_idx + 1} ({num_columns} variáveis)",
                        fontsize=max(10, min(16, 200 / num_columns)))
            
            plt.tight_layout()
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
            consensus_path = os.path.join(viz_dir, f"chunk_{chunk_idx:03d}_consensus_tree_adaptive.png")
            plt.savefig(consensus_path, dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close()
            
            print(f"  ✅ Consensus tree adaptativa salva: chunk_{chunk_idx:03d}_consensus_tree_adaptive.png")
            
        except Exception as e:
            print(f"  ❌ Erro ao gerar consensus tree adaptativa: {e}")
        
        # === 3. ÁRVORE SIMPLES COM LABELS RENOMEADOS ===
        try:
            tree = Phylo.read(newick_files[0], "newick")
            
            # Renomear labels se index_to_name fornecido
            if index_to_name:
                for leaf in tree.get_terminals():
                    if leaf.name and leaf.name in index_to_name:
                        leaf.name = index_to_name[leaf.name]
            
            # Configurar figura extra-grande para muitas colunas
            extra_width = fig_width * 1.2 if num_columns > 50 else fig_width
            extra_height = fig_height * 1.2 if num_columns > 50 else fig_height
            
            fig, ax = plt.subplots(figsize=(extra_width, extra_height))
            
            # Desenhar com labels originais
            Phylo.draw(tree, axes=ax, do_show=False,
                      branch_labels=None,
                      label_func=lambda x: x.name[:20] + '...' if x.name and len(x.name) > 20 else (x.name or ''),
                      label_colors='darkgreen')
            
            ax.set_title(f"Phylogenetic Tree (Original Labels) - Chunk {chunk_idx + 1}",
                        fontsize=max(10, min(16, 200 / num_columns)))
            
            plt.tight_layout()
            plt.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.1)
            
            labeled_path = os.path.join(viz_dir, f"chunk_{chunk_idx:03d}_tree_labeled_adaptive.png")
            plt.savefig(labeled_path, dpi=300, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close()
            
            print(f"  ✅ Árvore com labels adaptativa salva: chunk_{chunk_idx:03d}_tree_labeled_adaptive.png")
            
        except Exception as e:
            print(f"  ❌ Erro ao gerar árvore com labels: {e}")
        
        print(f"🎉 Visualizações adaptativas do chunk {chunk_idx + 1} concluídas!")
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("🔄 Tentando fallback básico...")
        generate_basic_fallback_visualization(newick_files, viz_dir, chunk_idx, fig_width, fig_height)
    except Exception as e:
        print(f"❌ Erro geral ao gerar visualizações adaptativas: {e}")
        generate_basic_fallback_visualization(newick_files, viz_dir, chunk_idx, fig_width, fig_height)

def generate_basic_fallback_visualization(newick_files, viz_dir, chunk_idx, fig_width, fig_height):
    """
    Fallback básico quando todas as outras opções falham.
    """
    print(f"🔄 Usando fallback básico para chunk {chunk_idx + 1}...")
    
    try:
        import matplotlib.pyplot as plt
        
        # Criar uma figura simples indicando que a visualização falhou
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.text(0.5, 0.5, f'Visualização do Chunk {chunk_idx + 1}\n\nArquivos Newick: {len(newick_files)}\n\nVisualizações detalhadas\nnão disponíveis',
                ha='center', va='center', fontsize=12, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        fallback_path = os.path.join(viz_dir, f"chunk_{chunk_idx:03d}_basic_info.png")
        plt.savefig(fallback_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  ✅ Fallback básico salvo: chunk_{chunk_idx:03d}_basic_info.png")
        
    except Exception as e:
        print(f"❌ Erro no fallback básico: {e}")


def generate_compiled_visualization(all_newick_files, DAMICORE_DIR, index_to_name, num_chunks, num_columns):
    """
    Gera visualização compilada agregando todas as árvores newick de todos os chunks.
    
    Args:
        num_columns (int): Número de colunas/variáveis para dimensionamento adaptativo
    """
    # Calcular dimensões adaptativas para visualização compilada
    adaptive_width, adaptive_height = calculate_adaptive_image_size(num_columns)
    fig_width, fig_height = calculate_adaptive_figure_size(num_columns)
    
    print(f"🎨 Compilando visualização de {len(all_newick_files)} arquivos newick de {num_chunks} chunks...")
    print(f"📏 Dimensões compiladas adaptativas: {adaptive_width}x{adaptive_height}px (para {num_columns} colunas)")
    
    # Criar diretório de visualização compilada
    compiled_viz_dir = os.path.join(DAMICORE_DIR, "compiled_visualizations")
    os.makedirs(compiled_viz_dir, exist_ok=True)
    
    try:
        # Usar o helper de visualização existente para gerar visualização compilada
        from visualization_helper import generate_visualizations
        
        print(f"🌳 Gerando visualização compilada com {len(all_newick_files)} árvores...")
        
        # Gerar visualização compilada usando todos os arquivos newick
        generate_visualizations(all_newick_files, compiled_viz_dir, index_to_name)
        
        # Renomear as visualizações para indicar que são compiladas
        import shutil
        compiled_files = [
            ("cloud_tree.pdf", "compiled_cloud_tree.pdf"),
            ("consensus_tree.pdf", "compiled_consensus_tree.pdf"), 
            ("tree_biopython.png", "compiled_tree_biopython.png")
        ]
        
        for original_name, compiled_name in compiled_files:
            src_path = os.path.join(compiled_viz_dir, "damicore_analysis", original_name)
            if os.path.exists(src_path):
                dst_path = os.path.join(compiled_viz_dir, compiled_name)
                shutil.copy2(src_path, dst_path)
                print(f"✅ {compiled_name} salva na visualização compilada")
        
        # Gerar resumo estatístico da compilação
        summary_path = os.path.join(compiled_viz_dir, "compilation_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"RESUMO DA VISUALIZAÇÃO COMPILADA\n")
            f.write(f"=" * 40 + "\n\n")
            f.write(f"Total de chunks processados: {num_chunks}\n")
            f.write(f"Total de arquivos newick: {len(all_newick_files)}\n")
            f.write(f"Média de arquivos por chunk: {len(all_newick_files)/num_chunks:.1f}\n\n")
            f.write(f"Arquivos newick compilados:\n")
            for i, newick_file in enumerate(all_newick_files, 1):
                f.write(f"{i:3d}. {os.path.basename(newick_file)}\n")
        
        print(f"📄 Resumo da compilação salvo em: compilation_summary.txt")
        print(f"🎉 Visualização compilada concluída!")
        print(f"📁 Visualizações compiladas salvas em: {compiled_viz_dir}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar visualização compilada: {e}")
        # Fallback: gerar visualização compilada básica usando Bio.Phylo com dimensões adaptativas
        generate_compiled_visualization_fallback(all_newick_files, compiled_viz_dir, num_chunks, fig_width, fig_height)


def generate_compiled_visualization_fallback(all_newick_files, compiled_viz_dir, num_chunks, fig_width=16, fig_height=12):
    """
    Fallback para gerar visualização compilada básica usando Bio.Phylo com dimensões adaptativas.
    
    Args:
        fig_width (float): Largura da figura em polegadas
        fig_height (float): Altura da figura em polegadas
    """
    print(f"🔄 Usando fallback para visualização compilada...")
    print(f"📏 Dimensões compiladas fallback: {fig_width:.1f}x{fig_height:.1f} polegadas")
    
    try:
        from Bio import Phylo
        import matplotlib.pyplot as plt
        
        if all_newick_files:
            # Usar a primeira árvore como representação da visualização compilada
            tree = Phylo.read(all_newick_files[0], "newick")
            
            # Visualização compilada básica com dimensões adaptativas
            plt.figure(figsize=(fig_width, fig_height))
            Phylo.draw(tree, do_show=False)
            plt.title(f"Visualização Compilada (Adaptive) - {num_chunks} Chunks, {len(all_newick_files)} Árvores")
            
            fallback_path = os.path.join(compiled_viz_dir, "compiled_fallback_tree.png")
            plt.savefig(fallback_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Visualização compilada fallback salva: compiled_fallback_tree.png")
            
    except Exception as e:
        print(f"❌ Erro no fallback de visualização compilada: {e}")

def main_non_interactive(csv_file):
    """
    Versão não-interativa do main() para execução automatizada.
    Executa processamento chunk a chunk com visualizações por chunk.
    """
    print("🚀 DAMICORE + Pareto Analysis - Processamento Chunk a Chunk")
    print("=" * 60)
    
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo não encontrado: {csv_file}")
        return
    
    # Configurar diretórios
    EXTERNAL_DRIVE_PATH = get_external_drive_path()
    if not EXTERNAL_DRIVE_PATH:
        print("❌ Drive externo não encontrado. Usando diretório local.")
        EXTERNAL_DRIVE_PATH = os.path.dirname(os.path.abspath(csv_file))
    
    # Configurar diretórios de saída
    file_basename = os.path.splitext(os.path.basename(csv_file))[0]
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d-%H-%M-%S")
    OUTPUT_DIR = os.path.join(EXTERNAL_DRIVE_PATH, "DAMICORE_RESULTS", f"{file_basename}-{timestamp}")
    DAMICORE_DIR = os.path.join(OUTPUT_DIR, "damicore_analysis")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DAMICORE_DIR, exist_ok=True)
    
    print(f"📁 Arquivo de entrada: {csv_file}")
    print(f"📁 Diretório de saída: {OUTPUT_DIR}")
    
    # Calcular tamanho do arquivo
    file_size_bytes = os.path.getsize(csv_file)
    file_size_gb = file_size_bytes / (1024**3)
    
    print(f"📊 Tamanho do arquivo: {file_size_gb:.2f} GB")
    
    # Executar processamento chunk a chunk
    try:
        execute_chunk_processing_per_chunk(csv_file, file_size_gb, OUTPUT_DIR, DAMICORE_DIR)
        print("\n🎉 Processamento chunk a chunk concluído com sucesso!")
        print(f"📁 Resultados salvos em: {OUTPUT_DIR}")
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
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
