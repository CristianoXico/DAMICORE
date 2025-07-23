#!/usr/bin/env python3
"""
Script de Teste de Tamanhos de Chunk para DAMICORE V2

Este script testa a NOVA ABORDAGEM V2:
- Menos linhas por chunk
- TODAS as colunas processadas de uma vez (sem lotes)
- Otimização de memória e estabilidade
- Mais fiel ao comportamento original do DAMICORE

Testa diferentes configurações de chunk_size para otimizar:
- Uso de memória
- Tempo de processamento
- Eficiência de I/O
- Estabilidade do sistema

Autor: DAMICORE Team
Data: 2025 - V2 (Nova Abordagem)
"""

import os
import sys
import time
import psutil
import pandas as pd
import subprocess
import tempfile
from pathlib import Path

# Configurações de teste para ABORDAGEM V2
# Nova estratégia: menos linhas por chunk, TODAS as colunas de uma vez
TEST_CHUNK_SIZES = [
    50,       # ULTRA-CONSERVADOR (para arquivos >15GB)
    100,      # CONSERVADOR (para arquivos >10GB) - baseado em testes reais
    200,      # BALANCEADO (para arquivos 5-10GB)
    500,      # PERFORMANCE (para arquivos 1-5GB) - baseado em testes reais
    1_000,    # LIMITE CRÍTICO (baseado em testes reais: 6.3GB RAM)
    2_000,    # TRADICIONAL (para arquivos <1GB)
    5_000,    # TESTE DE LIMITE (esperado: OOM em arquivos grandes)
]

BOOTSTRAP_SAMPLES = 2  # Reduzido para testes mais rápidos

# Configuração V2: TODAS as colunas processadas de uma vez
PROCESS_ALL_COLUMNS = True  # Nova abordagem: sem lotes de colunas

def get_memory_usage():
    """Retorna uso atual de memória em MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def get_system_memory():
    """Retorna informações de memória do sistema"""
    mem = psutil.virtual_memory()
    return {
        'total': mem.total / 1024 / 1024 / 1024,  # GB
        'available': mem.available / 1024 / 1024 / 1024,  # GB
        'percent': mem.percent
    }

def test_chunk_processing(csv_file, chunk_size, test_dir):
    """
    Testa processamento com um tamanho específico de chunk
    ABORDAGEM V2: Processa TODAS as colunas de uma vez
    Retorna métricas de desempenho
    """
    print(f"\n🧪 Testando chunk_size = {chunk_size:,} (V2: TODAS as colunas)")
    
    # Métricas iniciais
    start_time = time.time()
    initial_memory = get_memory_usage()
    max_memory = initial_memory
    
    # Diretório de teste
    chunk_test_dir = os.path.join(test_dir, f"chunk_{chunk_size}")
    os.makedirs(chunk_test_dir, exist_ok=True)
    
    chunks_processed = 0
    total_rows = 0
    total_columns = 0
    
    try:
        # Simular processamento em chunks (sem executar DAMICORE completo)
        for chunk_idx, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size)):
            chunks_processed += 1
            total_rows += len(chunk)
            total_columns = len(chunk.columns)  # Todas as colunas
            
            print(f"   📊 Chunk {chunk_idx}: {len(chunk)} linhas, {total_columns} colunas")
            
            # Simular processamento de bootstrap
            resampled_chunks = [chunk.copy()]
            for i in range(BOOTSTRAP_SAMPLES):
                bootstrap_sample = chunk.sample(n=len(chunk), replace=True, random_state=i)
                resampled_chunks.append(bootstrap_sample)
            
            # V2: Simular salvamento de TODAS as colunas (não apenas 5)
            for idx, resampled_df in enumerate(resampled_chunks):
                sample_dir = os.path.join(chunk_test_dir, f"chunk_{chunk_idx}_resample_{idx:02d}")
                os.makedirs(sample_dir, exist_ok=True)
                
                # V2: Processar TODAS as colunas de uma vez
                if PROCESS_ALL_COLUMNS:
                    # Salvar todas as colunas (simulação mais realista)
                    for col in resampled_df.columns:
                        col_path = os.path.join(sample_dir, f"col_{col}.txt")
                        resampled_df[col].to_csv(col_path, index=False, header=False)
                else:
                    # Fallback: apenas algumas colunas para teste rápido
                    test_columns = resampled_df.columns[:min(5, len(resampled_df.columns))]
                    for col in test_columns:
                        col_path = os.path.join(sample_dir, f"col_{col}.txt")
                        resampled_df[col].to_csv(col_path, index=False, header=False)
            
            # Monitorar uso de memória
            current_memory = get_memory_usage()
            max_memory = max(max_memory, current_memory)
            
            # Limpeza de memória
            del resampled_chunks
            del chunk
            import gc
            gc.collect()
            
            # Limite de teste para não demorar muito
            if chunks_processed >= 10:  # Testa apenas os primeiros 10 chunks
                break
                
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return None
    
    # Métricas finais
    end_time = time.time()
    final_memory = get_memory_usage()
    
    metrics = {
        'chunk_size': chunk_size,
        'success': True,
        'chunks_processed': chunks_processed,
        'total_rows': total_rows,
        'total_columns': total_columns,  # V2: incluir número de colunas
        'elapsed_time': end_time - start_time,
        'initial_memory': initial_memory,
        'max_memory': max_memory,
        'memory_delta': max_memory - initial_memory,
        'rows_per_second': total_rows / (end_time - start_time) if (end_time - start_time) > 0 else 0,
        'columns_per_chunk': total_columns if PROCESS_ALL_COLUMNS else 5,  # V2
        'approach': 'V2 (Todas as colunas)' if PROCESS_ALL_COLUMNS else 'V1 (5 colunas)',
        'status': 'COMPLETED'
    }
    
    print(f"  ✅ Processados: {chunks_processed} chunks, {total_rows:,} linhas")
    print(f"  ⏱️  Tempo: {metrics['elapsed_time']:.2f}s")
    print(f"  🧠 Memória: {metrics['memory_delta']:.1f} MB (pico: {max_memory:.1f} MB)")
    print(f"  📊 Performance: {metrics['rows_per_second']:.0f} linhas/s")
    
    return metrics

def run_chunk_size_tests(csv_file):
    """Executa todos os testes de chunk_size"""
    print("🚀 INICIANDO TESTES DE TAMANHO DE CHUNK")
    print("=" * 60)
    
    # Informações do arquivo
    file_size_gb = os.path.getsize(csv_file) / (1024**3)
    print(f"📁 Arquivo: {csv_file}")
    print(f"📏 Tamanho: {file_size_gb:.2f} GB")
    
    # Informações do sistema
    sys_mem = get_system_memory()
    print(f"🖥️  Memória do sistema: {sys_mem['total']:.1f} GB total, {sys_mem['available']:.1f} GB disponível")
    
    # Diretório de teste temporário
    with tempfile.TemporaryDirectory(prefix="damicore_chunk_test_") as test_dir:
        print(f"📂 Diretório de teste: {test_dir}")
        
        results = []
        
        # Executar testes para cada chunk_size
        for chunk_size in TEST_CHUNK_SIZES:
            # Verificar se há memória suficiente
            if sys_mem['available'] < 1.0:  # Menos de 1GB disponível
                print(f"⚠️  Pulando chunk_size {chunk_size:,} - pouca memória disponível")
                continue
                
            metrics = test_chunk_processing(csv_file, chunk_size, test_dir)
            if metrics:
                results.append(metrics)
                
                # Parar se uso de memória for muito alto
                if metrics['max_memory'] > sys_mem['total'] * 1024 * 0.8:  # 80% da RAM total
                    print(f"⚠️  Parando testes - uso de memória muito alto ({metrics['max_memory']:.1f} MB)")
                    break
        
        # Análise dos resultados
        analyze_results(results, file_size_gb)

def analyze_results(results, file_size_gb):
    """Analisa os resultados dos testes e fornece recomendações para ABORDAGEM V2"""
    if not results:
        print("\n⚠️  Nenhum resultado para analisar")
        return
    
    print("\n📊 RESULTADOS DOS TESTES - ABORDAGEM V2")
    print("=" * 70)
    print(f"Abordagem: {'V2 - Todas as colunas processadas de uma vez' if PROCESS_ALL_COLUMNS else 'V1 - Apenas 5 colunas'}")
    print("=" * 70)
    
    # Cabeçalho da tabela
    print(f"{'Chunk':<8} {'Chunks':<7} {'Linhas':<8} {'Colunas':<8} {'Tempo(s)':<8} {'Mem(MB)':<8} {'L/s':<6} {'Status':<10}")
    print("-" * 70)
    
    # Resultados individuais
    for result in results:
        status = result.get('status', 'UNKNOWN')
        columns = result.get('total_columns', 'N/A')
        print(f"{result['chunk_size']:<8,} "
              f"{result['chunks_processed']:<7} "
              f"{result['total_rows']:<8,} "
              f"{columns:<8} "
              f"{result['elapsed_time']:<8.1f} "
              f"{result['memory_delta']:<8.1f} "
              f"{result['rows_per_second']:<6.0f} "
              f"{status:<10}")
    
    print("\n🏆 RECOMENDAÇÕES PARA ABORDAGEM V2")
    print("=" * 50)
    
    # Melhor para velocidade
    fastest = min(results, key=lambda x: x['elapsed_time'])
    print(f"⚡ Mais rápido: chunk_size = {fastest['chunk_size']:,} "
          f"({fastest['rows_per_second']:.0f} linhas/s)")
    
    # Melhor para memória
    lowest_memory = min(results, key=lambda x: x['memory_delta'])
    print(f"🧠 Menor uso de memória: chunk_size = {lowest_memory['chunk_size']:,} "
          f"({lowest_memory['memory_delta']:.1f} MB)")
    
    # Melhor eficiência (linhas/s por MB usado)
    for r in results:
        r['efficiency'] = r['rows_per_second'] / max(r['memory_delta'], 1)
    
    most_efficient = max(results, key=lambda x: x['efficiency'])
    print(f"⚖️  Mais eficiente: chunk_size = {most_efficient['chunk_size']:,} "
          f"(eficiência: {most_efficient['efficiency']:.1f})")
    
    # Recomendação baseada no tamanho do arquivo (ABORDAGEM V2)
    print(f"\n📝 RECOMENDAÇÃO V2 PARA ARQUIVO DE {file_size_gb:.1f} GB:")
    print("(Nova estratégia: menos linhas, TODAS as colunas processadas)")
    
    if file_size_gb >= 10:
        recommended_chunks = [50, 100, 200]
        print("🔴 Arquivo muito grande (>=10GB) - ABORDAGEM V2:")
        print("   - Use chunk_size entre 50-200 (baseado em testes reais)")
        print("   - chunk_size=100: 18 linhas/s, 1.1GB RAM (CONSERVADOR)")
        print("   - chunk_size=500: 30 linhas/s, 3.6GB RAM (PERFORMANCE)")
        print("   - Processa TODAS as colunas de uma vez")
    elif file_size_gb >= 1:
        recommended_chunks = [200, 500, 1000]
        print("🟡 Arquivo grande (1-10GB) - ABORDAGEM V2:")
        print("   - Use chunk_size entre 200-1000 para bom balance")
        print("   - Processa TODAS as colunas simultaneamente")
    else:
        recommended_chunks = [1000, 2000, 5000]
        print("🟢 Arquivo pequeno (<1GB) - ABORDAGEM V2:")
        print("   - Use chunk_size entre 1000-5000 para máxima velocidade")
        print("   - Processa TODAS as colunas de uma vez")
    
    # Verificar se alguma recomendação foi testada
    tested_recommended = [r for r in results if r['chunk_size'] in recommended_chunks]
    if tested_recommended:
        best_recommended = min(tested_recommended, key=lambda x: x['elapsed_time'])
        print(f"\n✅ Melhor opção V2 testada: chunk_size = {best_recommended['chunk_size']:,}")
        print(f"   Performance: {best_recommended['rows_per_second']:.0f} linhas/s, {best_recommended['memory_delta']:.1f} MB")

def main():
    if len(sys.argv) != 2:
        print("Uso: python test_chunk_sizes.py <arquivo.csv>")
        print("\nExemplo:")
        print("python test_chunk_sizes.py /path/to/dataset.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo não encontrado: {csv_file}")
        sys.exit(1)
    
    run_chunk_size_tests(csv_file)

if __name__ == "__main__":
    main()
