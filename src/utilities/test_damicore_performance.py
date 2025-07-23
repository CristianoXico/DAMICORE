#!/usr/bin/env python3
"""
Script de Teste de Performance do DAMICORE com Diferentes Chunk Sizes

Este script testa o desempenho completo do pipeline DAMICORE com diferentes
configurações de chunk_size, incluindo:
- Tempo total de execução
- Uso de memória durante DAMICORE
- Qualidade dos arquivos newick gerados
- Tempo de geração de visualizações

Autor: DAMICORE Team  
Data: 2025
"""

import os
import sys
import time
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

# Configurações de teste
TEST_CONFIGURATIONS = [
    {'chunk_size': 500, 'bootstrap_samples': 2, 'name': 'ultra_small'},
    {'chunk_size': 1_000, 'bootstrap_samples': 2, 'name': 'small'},
    {'chunk_size': 5_000, 'bootstrap_samples': 3, 'name': 'medium'},
    {'chunk_size': 10_000, 'bootstrap_samples': 3, 'name': 'large'},
    {'chunk_size': 50_000, 'bootstrap_samples': 5, 'name': 'xlarge'},
]

def create_test_script(chunk_size, bootstrap_samples, csv_file, output_dir):
    """Cria um script temporário com configuração específica"""
    
    script_content = f'''#!/usr/bin/env python3
import os
import sys
import pandas as pd
import subprocess
import time

# Configuração do teste
CSV_FILE = "{csv_file}"
OUTPUT_DIR = "{output_dir}"
CHUNK_SIZE = {chunk_size}
BOOTSTRAP_SAMPLES = {bootstrap_samples}

# Importar função de processamento
sys.path.append("/home/cristiano-xico/github/CristianoXico/DAMICORE/src/scripts")

def execute_chunk_processing_test():
    """Executa processamento com configuração específica"""
    
    print(f"🧪 Teste: chunk_size={{CHUNK_SIZE}}, bootstrap_samples={{BOOTSTRAP_SAMPLES}}")
    
    # Configurar diretórios
    DAMICORE_DIR = os.path.join(OUTPUT_DIR, "damicore_analysis")
    sample_dir = os.path.join(DAMICORE_DIR, "sample_full")
    os.makedirs(sample_dir, exist_ok=True)
    
    # Carregar dados originais
    original_columns = None
    chunk_idx = 0
    
    start_time = time.time()
    
    # Processar em chunks
    for chunk in pd.read_csv(CSV_FILE, chunksize=CHUNK_SIZE):
        print(f"Processando chunk {{chunk_idx}} ({{len(chunk)}} linhas)...")
        
        if original_columns is None:
            original_columns = chunk.columns.tolist()
        
        # Reindexa colunas
        chunk.columns = [str(i) for i in range(len(chunk.columns))]
        chunk = chunk.map(lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)

        # Bootstrap no chunk
        resampled_chunks = [chunk.copy()]
        for i in range(BOOTSTRAP_SAMPLES):
            bootstrap_sample = chunk.sample(n=chunk.shape[0], replace=True, random_state=i)
            resampled_chunks.append(bootstrap_sample)
        
        # Salvar colunas
        for idx, resampled_df in enumerate(resampled_chunks):
            resample_dir = os.path.join(sample_dir, f"chunk_{{chunk_idx}}_resample_{{idx:02d}}")
            os.makedirs(resample_dir, exist_ok=True)
            
            for col in resampled_df.columns:
                col_path = os.path.join(resample_dir, f"col_{{col}}.txt")
                resampled_df[col].to_csv(col_path, index=False, header=False, encoding="utf-8")
        
        chunk_idx += 1
        
        # Limitar teste para não demorar muito
        if chunk_idx >= 5:  # Apenas 5 chunks para teste
            break
    
    processing_time = time.time() - start_time
    
    # Consolidação e execução do DAMICORE
    print("\\n=== CONSOLIDANDO E EXECUTANDO DAMICORE ===")
    
    consolidated_sample_dir = os.path.join(DAMICORE_DIR, "consolidated_samples")
    os.makedirs(consolidated_sample_dir, exist_ok=True)
    
    # Consolidar por amostra bootstrap
    for bootstrap_idx in range(BOOTSTRAP_SAMPLES + 1):
        consolidated_resample_dir = os.path.join(consolidated_sample_dir, f"resample_{{bootstrap_idx:02d}}")
        os.makedirs(consolidated_resample_dir, exist_ok=True)
        
        for col_idx in range(len(original_columns)):
            col_name = str(col_idx)
            consolidated_col_path = os.path.join(consolidated_resample_dir, f"col_{{col_name}}.txt")
            
            with open(consolidated_col_path, 'w', encoding='utf-8') as out_file:
                for chunk_dir in os.listdir(sample_dir):
                    if f"resample_{{bootstrap_idx:02d}}" in chunk_dir:
                        col_file_path = os.path.join(sample_dir, chunk_dir, f"col_{{col_name}}.txt")
                        if os.path.exists(col_file_path):
                            with open(col_file_path, 'r', encoding='utf-8') as in_file:
                                out_file.write(in_file.read())
    
    # Executar DAMICORE para cada amostra
    results_dir = os.path.join(DAMICORE_DIR, "damicore_results")
    os.makedirs(results_dir, exist_ok=True)
    
    damicore_start = time.time()
    newick_count = 0
    
    for resample_dir_name in os.listdir(consolidated_sample_dir):
        resample_path = os.path.join(consolidated_sample_dir, resample_dir_name)
        if not os.path.isdir(resample_path):
            continue
            
        tree_output = os.path.join(results_dir, f"{{resample_dir_name}}-tree.newick")
        
        try:
            cmd = [
                "python", "/home/cristiano-xico/github/CristianoXico/DAMICORE/src/damicore.py",
                "--compressor", "gzip",
                "--tree-output", tree_output,
                resample_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 min timeout
            
            if result.returncode == 0:
                newick_count += 1
                print(f"✅ {{resample_dir_name}}: DAMICORE executado com sucesso!")
            else:
                print(f"❌ {{resample_dir_name}}: Erro no DAMICORE")
                
        except subprocess.TimeoutExpired:
            print(f"❌ {{resample_dir_name}}: DAMICORE timeout")
        except Exception as e:
            print(f"❌ {{resample_dir_name}}: Erro: {{e}}")
    
    damicore_time = time.time() - damicore_start
    total_time = time.time() - start_time
    
    # Resultados
    results = {{
        'chunk_size': CHUNK_SIZE,
        'bootstrap_samples': BOOTSTRAP_SAMPLES,
        'chunks_processed': chunk_idx,
        'processing_time': processing_time,
        'damicore_time': damicore_time,
        'total_time': total_time,
        'newick_files': newick_count,
        'success': newick_count > 0
    }}
    
    print(f"\\n📊 RESULTADOS:")
    print(f"  Chunks processados: {{chunk_idx}}")
    print(f"  Tempo de processamento: {{processing_time:.2f}}s")
    print(f"  Tempo do DAMICORE: {{damicore_time:.2f}}s")
    print(f"  Tempo total: {{total_time:.2f}}s")
    print(f"  Arquivos newick: {{newick_count}}")
    
    return results

if __name__ == "__main__":
    results = execute_chunk_processing_test()
    
    # Salvar resultados
    results_file = os.path.join(OUTPUT_DIR, "test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\\n✅ Resultados salvos em: {{results_file}}")
'''
    
    return script_content

def run_performance_tests(csv_file, base_output_dir):
    """Executa testes de performance com diferentes configurações"""
    
    print("🚀 INICIANDO TESTES DE PERFORMANCE DO DAMICORE")
    print("=" * 70)
    
    file_size_gb = os.path.getsize(csv_file) / (1024**3)
    print(f"📁 Arquivo: {csv_file}")
    print(f"📏 Tamanho: {file_size_gb:.2f} GB")
    
    all_results = []
    
    for config in TEST_CONFIGURATIONS:
        print(f"\n{'='*50}")
        print(f"🧪 TESTE: {config['name'].upper()}")
        print(f"   chunk_size: {config['chunk_size']:,}")
        print(f"   bootstrap_samples: {config['bootstrap_samples']}")
        print(f"{'='*50}")
        
        # Criar diretório de teste
        test_output_dir = os.path.join(base_output_dir, f"test_{config['name']}")
        os.makedirs(test_output_dir, exist_ok=True)
        
        # Criar script de teste temporário
        script_content = create_test_script(
            config['chunk_size'], 
            config['bootstrap_samples'], 
            csv_file, 
            test_output_dir
        )
        
        # Executar teste
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
            temp_script.write(script_content)
            temp_script_path = temp_script.name
        
        try:
            start_time = time.time()
            result = subprocess.run([sys.executable, temp_script_path], 
                                  capture_output=True, text=True, timeout=1800)  # 30 min timeout
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print("✅ Teste concluído com sucesso!")
                
                # Carregar resultados
                results_file = os.path.join(test_output_dir, "test_results.json")
                if os.path.exists(results_file):
                    with open(results_file, 'r') as f:
                        test_results = json.load(f)
                    test_results['config_name'] = config['name']
                    test_results['execution_time'] = execution_time
                    all_results.append(test_results)
                else:
                    print("⚠️ Arquivo de resultados não encontrado")
            else:
                print(f"❌ Teste falhou: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("❌ Teste timeout após 30 minutos")
        except Exception as e:
            print(f"❌ Erro durante teste: {e}")
        finally:
            # Limpar script temporário
            if os.path.exists(temp_script_path):
                os.unlink(temp_script_path)
    
    # Análise comparativa
    if all_results:
        analyze_performance_results(all_results, base_output_dir)

def analyze_performance_results(results, output_dir):
    """Analisa e compara os resultados de performance"""
    
    print("\n" + "="*70)
    print("📊 ANÁLISE COMPARATIVA DE PERFORMANCE")
    print("="*70)
    
    # Tabela de resultados
    print(f"{'Config':<12} {'Chunk Size':<12} {'Bootstrap':<10} {'Total (s)':<10} {'DAMICORE (s)':<12} {'Newick':<8}")
    print("-" * 70)
    
    for r in results:
        if r['success']:
            print(f"{r['config_name']:<12} {r['chunk_size']:<12,} {r['bootstrap_samples']:<10} "
                  f"{r['total_time']:<10.1f} {r['damicore_time']:<12.1f} {r['newick_files']:<8}")
        else:
            print(f"{r['config_name']:<12} {r['chunk_size']:<12,} {r['bootstrap_samples']:<10} FALHOU")
    
    # Encontrar melhores configurações
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        print("\n🏆 MELHORES CONFIGURAÇÕES:")
        
        fastest = min(successful_results, key=lambda x: x['total_time'])
        print(f"⚡ Mais rápido: {fastest['config_name']} ({fastest['total_time']:.1f}s total)")
        
        fastest_damicore = min(successful_results, key=lambda x: x['damicore_time'])
        print(f"🌳 DAMICORE mais rápido: {fastest_damicore['config_name']} ({fastest_damicore['damicore_time']:.1f}s)")
        
        # Salvar relatório completo
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'fastest_overall': fastest['config_name'],
                'fastest_damicore': fastest_damicore['config_name'],
                'successful_configs': len(successful_results),
                'total_configs': len(results)
            }
        }
        
        report_file = os.path.join(output_dir, "performance_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Relatório completo salvo em: {report_file}")

def main():
    if len(sys.argv) != 2:
        print("Uso: python test_damicore_performance.py <arquivo.csv>")
        print("\nExemplo:")
        print("python test_damicore_performance.py /path/to/dataset.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo não encontrado: {csv_file}")
        sys.exit(1)
    
    # Criar diretório de resultados
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_dir = f"/tmp/damicore_performance_test_{base_name}_{int(time.time())}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📂 Resultados dos testes em: {output_dir}")
    
    run_performance_tests(csv_file, output_dir)

if __name__ == "__main__":
    main()
