#!/usr/bin/env python3
"""
Exemplo de uso da funcionalidade de retomada automática do DAMICORE
"""

import os
from streaming_processor import process_file_streaming
from resume_processor import get_progress_summary

def main():
    # Configurações do exemplo
    file_path = "/media/cristiano-xico/sandbox/test_dataset.csv"
    chunk_size = 100
    bootstrap_samples = 2
    max_columns_per_batch = None  # V2: processar todas as colunas de uma vez
    
    # Diretórios
    external_drive_path = "/media/cristiano-xico/sandbox"
    dataset_name = "test_dataset"
    sample_dir = os.path.join(external_drive_path, "DAMICORE_RESULTS", dataset_name, "samples")
    damicore_dir = os.path.join(external_drive_path, "DAMICORE_RESULTS", dataset_name, "damicore_analysis")
    
    print("🔄 EXEMPLO DE RETOMADA AUTOMÁTICA DO DAMICORE")
    print("=" * 50)
    
    # Mostra progresso atual (se existir)
    if os.path.exists(damicore_dir):
        progress_summary = get_progress_summary(damicore_dir)
        print(f"📊 {progress_summary}")
    else:
        print("📊 Nenhum progresso anterior encontrado - iniciando do zero")
    
    print()
    print("🚀 Iniciando processamento com retomada automática...")
    print(f"📁 Arquivo: {file_path}")
    print(f"📦 Chunk size: {chunk_size}")
    print(f"🔄 Bootstrap samples: {bootstrap_samples}")
    print(f"🎯 Abordagem: V2 (todas as colunas por chunk)")
    print()
    
    # Executa processamento com retomada automática
    try:
        newick_files = process_file_streaming(
            file_path=file_path,
            chunk_size=chunk_size,
            bootstrap_samples=bootstrap_samples,
            max_columns_per_batch=max_columns_per_batch,
            sample_dir=sample_dir,
            damicore_dir=damicore_dir,
            external_drive_path=external_drive_path
        )
        
        print()
        print("✅ PROCESSAMENTO CONCLUÍDO!")
        print(f"🌳 Total de arquivos newick: {len(newick_files)}")
        
        # Mostra progresso final
        progress_summary = get_progress_summary(damicore_dir)
        print(f"📊 {progress_summary}")
        
    except KeyboardInterrupt:
        print()
        print("⚠️  Processamento interrompido pelo usuário")
        print("🔄 Na próxima execução, o processamento continuará de onde parou!")
        
        if os.path.exists(damicore_dir):
            progress_summary = get_progress_summary(damicore_dir)
            print(f"📊 {progress_summary}")
    
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
        print("🔄 Na próxima execução, o processamento continuará de onde parou!")

if __name__ == "__main__":
    main()
