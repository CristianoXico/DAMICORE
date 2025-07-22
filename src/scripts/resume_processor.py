#!/usr/bin/env python3
"""
Módulo de Retomada Automática do Pipeline DAMICORE
Permite continuar processamento a partir do ponto onde parou
"""

import os
import json
from datetime import datetime
from pathlib import Path


def create_progress_file(damicore_dir, total_chunks, bootstrap_samples):
    """
    Cria arquivo de progresso inicial
    """
    progress_file = os.path.join(damicore_dir, "pipeline_progress.json")
    
    progress_data = {
        "total_chunks": total_chunks,
        "bootstrap_samples": bootstrap_samples,
        "completed_chunks": [],
        "completed_samples": {},  # chunk_idx: [lista de amostras completadas]
        "failed_chunks": [],
        "last_chunk_processed": -1,
        "pipeline_status": "running"
    }
    
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f, indent=2)
    
    print(f"📝 Arquivo de progresso criado: {progress_file}")
    return progress_file


def load_progress(damicore_dir):
    """
    Carrega progresso existente ou retorna None se não existir
    """
    progress_file = os.path.join(damicore_dir, "pipeline_progress.json")
    
    if not os.path.exists(progress_file):
        return None
    
    try:
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
        print(f"📂 Progresso carregado: {progress_file}")
        return progress_data
    except Exception as e:
        print(f"⚠️  Erro ao carregar progresso: {e}")
        return None


def scan_existing_results(damicore_dir):
    """
    Escaneia diretório de resultados para identificar chunks/amostras já processados
    """
    results_dir = os.path.join(damicore_dir, "damicore_results")
    
    if not os.path.exists(results_dir):
        return {}
    
    completed_samples = {}
    newick_files = []
    
    # Procura por arquivos newick existentes
    for file in os.listdir(results_dir):
        if file.endswith("-tree.newick"):
            newick_files.append(file)
            
            # Extrai chunk_idx e sample_idx do nome do arquivo
            # Formato: chunk_X_resample_YY-tree.newick
            try:
                parts = file.replace("-tree.newick", "").split("_")
                chunk_idx = int(parts[1])  # chunk_X
                sample_idx = int(parts[3])  # resample_YY
                
                if chunk_idx not in completed_samples:
                    completed_samples[chunk_idx] = []
                completed_samples[chunk_idx].append(sample_idx)
                
            except (IndexError, ValueError) as e:
                print(f"⚠️  Não foi possível parsear arquivo: {file} - {e}")
    
    # Ordena as amostras para cada chunk
    for chunk_idx in completed_samples:
        completed_samples[chunk_idx].sort()
    
    print(f"🔍 Encontrados {len(newick_files)} arquivos newick existentes")
    for chunk_idx, samples in completed_samples.items():
        print(f"   Chunk {chunk_idx}: amostras {samples}")
    
    return completed_samples


def update_progress(damicore_dir, chunk_idx, sample_idx, status="completed"):
    """
    Atualiza progresso após completar um chunk/amostra
    """
    progress_file = os.path.join(damicore_dir, "pipeline_progress.json")
    
    # Carrega progresso atual
    progress_data = load_progress(damicore_dir)
    if not progress_data:
        return
    
    # Atualiza dados
    if chunk_idx not in progress_data["completed_samples"]:
        progress_data["completed_samples"][chunk_idx] = []
    
    if status == "completed":
        if sample_idx not in progress_data["completed_samples"][chunk_idx]:
            progress_data["completed_samples"][chunk_idx].append(sample_idx)
            progress_data["completed_samples"][chunk_idx].sort()
        
        # Atualiza último chunk processado
        progress_data["last_chunk_processed"] = max(
            progress_data["last_chunk_processed"], chunk_idx
        )
        
        # Verifica se chunk está completo
        expected_samples = list(range(progress_data["bootstrap_samples"]))
        if progress_data["completed_samples"][chunk_idx] == expected_samples:
            if chunk_idx not in progress_data["completed_chunks"]:
                progress_data["completed_chunks"].append(chunk_idx)
                progress_data["completed_chunks"].sort()
    
    elif status == "failed":
        if chunk_idx not in progress_data["failed_chunks"]:
            progress_data["failed_chunks"].append(chunk_idx)
    
    # Salva progresso
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f, indent=2)


def get_resume_point(damicore_dir, total_chunks, bootstrap_samples):
    """
    Determina de onde retomar o processamento
    Retorna (chunk_inicial, amostras_pendentes_por_chunk)
    """
    # Primeiro, escaneia resultados existentes
    existing_results = scan_existing_results(damicore_dir)
    
    # Carrega ou cria progresso
    progress_data = load_progress(damicore_dir)
    if not progress_data:
        progress_data = {
            "total_chunks": total_chunks,
            "bootstrap_samples": bootstrap_samples,
            "completed_chunks": [],
            "completed_samples": existing_results,
            "failed_chunks": [],
            "last_chunk_processed": -1,
            "pipeline_status": "running"
        }
        
        # Salva progresso inicial
        progress_file = os.path.join(damicore_dir, "pipeline_progress.json")
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    else:
        # Atualiza com resultados escaneados
        progress_data["completed_samples"] = existing_results
    
    # Verifica se pipeline já foi marcado como completado
    if progress_data.get("pipeline_status") == "completed":
        print("✅ Pipeline já foi completado anteriormente!")
        return None, {}
    
    # Calcula chunks e amostras pendentes
    pending_work = {}
    
    for chunk_idx in range(total_chunks):
        completed_samples = progress_data["completed_samples"].get(chunk_idx, [])
        expected_samples = list(range(bootstrap_samples))
        pending_samples = [s for s in expected_samples if s not in completed_samples]
        
        if pending_samples:
            pending_work[chunk_idx] = pending_samples
    
    # Determina ponto de retomada
    if not pending_work:
        print("✅ Todos os chunks já foram processados!")
        return None, {}
    
    first_pending_chunk = min(pending_work.keys())
    
    # Relatório de retomada
    total_pending = sum(len(samples) for samples in pending_work.values())
    total_completed = sum(len(samples) for samples in existing_results.values())
    
    print(f"🔄 RETOMADA AUTOMÁTICA DETECTADA")
    print(f"   ✅ Já processados: {total_completed} chunks/amostras")
    print(f"   ⏳ Pendentes: {total_pending} chunks/amostras")
    print(f"   🚀 Retomando a partir do chunk {first_pending_chunk}")
    
    for chunk_idx, pending_samples in list(pending_work.items())[:5]:  # Mostra primeiros 5
        print(f"      Chunk {chunk_idx}: amostras pendentes {pending_samples}")
    
    if len(pending_work) > 5:
        print(f"      ... e mais {len(pending_work) - 5} chunks pendentes")
    
    return first_pending_chunk, pending_work


def mark_pipeline_completed(damicore_dir):
    """
    Marca o pipeline como completamente finalizado.
    
    Args:
        damicore_dir: Diretório onde está o arquivo de progresso
    """
    progress_file = os.path.join(damicore_dir, "pipeline_progress.json")
    
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        
        progress['pipeline_status'] = 'completed'
        progress['completion_time'] = datetime.now().isoformat()
        
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        print(" Pipeline marcado como completamente finalizado!")


def get_progress_summary(damicore_dir):
    """
    Retorna um resumo do progresso atual do pipeline.
    
    Args:
        damicore_dir: Diretório onde está o arquivo de progresso
        
    Returns:
        str: Resumo do progresso em formato legível
    """
    progress_file = os.path.join(damicore_dir, "pipeline_progress.json")
    
    if not os.path.exists(progress_file):
        return "Nenhum progresso anterior encontrado"
    
    try:
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        
        if progress.get('completed', False):
            return "Pipeline já completado anteriormente"
        
        total_chunks = progress.get('total_chunks', 0)
        total_samples = progress.get('total_samples', 0)
        
        # Conta chunks e amostras completados
        completed_chunks = 0
        completed_samples = 0
        
        for chunk_idx in range(total_chunks):
            chunk_key = f"chunk_{chunk_idx}"
            if chunk_key in progress:
                chunk_data = progress[chunk_key]
                if chunk_data.get('completed', False):
                    completed_chunks += 1
                
                # Conta amostras completadas neste chunk
                for sample_idx in range(total_samples):
                    sample_key = f"sample_{sample_idx}"
                    if chunk_data.get(sample_key, {}).get('completed', False):
                        completed_samples += 1
        
        total_work = total_chunks * total_samples
        completion_pct = (completed_samples / total_work * 100) if total_work > 0 else 0
        
        return (f"Progresso: {completed_samples}/{total_work} amostras "
                f"({completion_pct:.1f}%) - {completed_chunks}/{total_chunks} chunks")
    
    except Exception as e:
        return f"Erro ao ler progresso: {e}"
