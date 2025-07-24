#!/usr/bin/env python3
"""
Debug script to diagnose why DAMICORE slices are not generating newick files.
This script will help identify the root cause of the newick generation failure.
"""

import os
import sys
import subprocess
import pandas as pd
import json
from pathlib import Path

def debug_slice_processing(slice_file_path):
    """
    Comprehensive debugging of a single slice to identify why newick files aren't generated.
    """
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE PROCESSAMENTO DE FATIA")
    print("=" * 80)
    
    slice_file = Path(slice_file_path)
    if not slice_file.exists():
        print(f"❌ Arquivo de fatia não encontrado: {slice_file_path}")
        return False
    
    print(f"📁 Arquivo de fatia: {slice_file_path}")
    
    # 1. Verificar conteúdo do arquivo CSV
    print("\n1️⃣ VERIFICANDO CONTEÚDO DO ARQUIVO CSV:")
    try:
        df = pd.read_csv(slice_file_path)
        print(f"   ✅ Linhas: {len(df)}")
        print(f"   ✅ Colunas: {len(df.columns)}")
        print(f"   ✅ Colunas: {list(df.columns)}")
        print(f"   ✅ Primeiras 3 linhas:")
        print(df.head(3))
        
        if len(df) < 3:
            print("   ⚠️  AVISO: Muito poucas linhas para análise DAMICORE")
        if len(df.columns) < 3:
            print("   ⚠️  AVISO: Muito poucas colunas para análise DAMICORE")
            
    except Exception as e:
        print(f"   ❌ Erro ao ler CSV: {e}")
        return False
    
    # 2. Verificar diretório de saída
    output_dir = slice_file.parent / slice_file.stem
    print(f"\n2️⃣ VERIFICANDO DIRETÓRIO DE SAÍDA:")
    print(f"   📁 Diretório esperado: {output_dir}")
    
    if output_dir.exists():
        print("   ✅ Diretório existe")
        files = list(output_dir.iterdir())
        print(f"   📄 Arquivos encontrados: {len(files)}")
        for f in files[:10]:  # Mostrar até 10 arquivos
            print(f"      - {f.name}")
        if len(files) > 10:
            print(f"      ... e mais {len(files) - 10} arquivos")
    else:
        print("   ❌ Diretório não existe")
    
    # 3. Verificar checkpoint
    checkpoint_file = output_dir / "filograma_checkpoint.json"
    print(f"\n3️⃣ VERIFICANDO CHECKPOINT:")
    if checkpoint_file.exists():
        print("   ✅ Checkpoint existe")
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            print(f"   📊 Status: {checkpoint.get('status', 'N/A')}")
            print(f"   📊 Etapas concluídas: {checkpoint.get('completed_steps', [])}")
            print(f"   📊 Amostras com falha: {len(checkpoint.get('failed_samples', []))}")
            
            if 'failed_samples' in checkpoint and checkpoint['failed_samples']:
                print("   ⚠️  Amostras que falharam:")
                for sample in checkpoint['failed_samples'][:5]:  # Mostrar até 5
                    print(f"      - {sample}")
                    
        except Exception as e:
            print(f"   ❌ Erro ao ler checkpoint: {e}")
    else:
        print("   ❌ Checkpoint não existe")
    
    # 4. Procurar arquivos newick
    print(f"\n4️⃣ PROCURANDO ARQUIVOS NEWICK:")
    newick_files = []
    if output_dir.exists():
        newick_files = list(output_dir.glob("*.newick"))
        newick_files.extend(list(output_dir.glob("**/*.newick")))  # Busca recursiva
    
    print(f"   🌳 Arquivos .newick encontrados: {len(newick_files)}")
    for nf in newick_files[:5]:  # Mostrar até 5
        print(f"      - {nf.name} ({nf.stat().st_size} bytes)")
    
    # 5. Procurar arquivos de amostra (bootstrap)
    print(f"\n5️⃣ VERIFICANDO ARQUIVOS DE AMOSTRA:")
    if output_dir.exists():
        sample_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith('resample_')]
        print(f"   📂 Diretórios de amostra encontrados: {len(sample_dirs)}")
        
        for sample_dir in sample_dirs[:3]:  # Verificar até 3 amostras
            print(f"      📁 {sample_dir.name}:")
            txt_files = list(sample_dir.glob("*.txt"))
            print(f"         - Arquivos .txt: {len(txt_files)}")
            
            # Verificar se DAMICORE foi executado nesta amostra
            damicore_output = list(sample_dir.glob("*tree*"))
            print(f"         - Arquivos de árvore: {len(damicore_output)}")
            for tree_file in damicore_output[:3]:
                print(f"           * {tree_file.name}")
    
    # 6. Testar execução manual do DAMICORE em uma amostra
    print(f"\n6️⃣ TESTE MANUAL DO DAMICORE:")
    if output_dir.exists():
        sample_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith('resample_')]
        if sample_dirs:
            test_sample = sample_dirs[0]
            print(f"   🧪 Testando amostra: {test_sample.name}")
            
            # Verificar arquivos .txt na amostra
            txt_files = list(test_sample.glob("*.txt"))
            if txt_files:
                print(f"   📄 Arquivos .txt disponíveis: {len(txt_files)}")
                
                # Tentar executar DAMICORE manualmente
                damicore_path = Path(__file__).parent.parent / "damicore.py"
                if damicore_path.exists():
                    print(f"   🔧 Executando DAMICORE em: {test_sample}")
                    try:
                        result = subprocess.run([
                            sys.executable, str(damicore_path), str(test_sample)
                        ], capture_output=True, text=True, timeout=60, cwd=test_sample)
                        
                        print(f"   📤 Código de saída: {result.returncode}")
                        if result.stdout:
                            print(f"   📤 STDOUT: {result.stdout[:500]}...")
                        if result.stderr:
                            print(f"   📤 STDERR: {result.stderr[:500]}...")
                            
                        # Verificar se arquivos foram gerados
                        after_files = list(test_sample.iterdir())
                        tree_files = [f for f in after_files if 'tree' in f.name.lower()]
                        print(f"   🌳 Arquivos de árvore após execução: {len(tree_files)}")
                        
                    except subprocess.TimeoutExpired:
                        print("   ⏰ Timeout na execução do DAMICORE")
                    except Exception as e:
                        print(f"   ❌ Erro na execução: {e}")
                else:
                    print(f"   ❌ DAMICORE não encontrado em: {damicore_path}")
            else:
                print("   ❌ Nenhum arquivo .txt encontrado na amostra")
        else:
            print("   ❌ Nenhum diretório de amostra encontrado")
    
    print("\n" + "=" * 80)
    print("🎯 RESUMO DO DIAGNÓSTICO:")
    print(f"   📁 Arquivo CSV: {'✅ OK' if df is not None else '❌ ERRO'}")
    print(f"   📂 Diretório saída: {'✅ OK' if output_dir.exists() else '❌ ERRO'}")
    print(f"   📋 Checkpoint: {'✅ OK' if checkpoint_file.exists() else '❌ ERRO'}")
    print(f"   🌳 Arquivos newick: {'✅ OK' if newick_files else '❌ ERRO'}")
    print("=" * 80)
    
    return len(newick_files) > 0

def main():
    if len(sys.argv) != 2:
        print("Uso: python debug_slice_processing.py <caminho_para_fatia.csv>")
        print("Exemplo: python debug_slice_processing.py /path/to/slice_0000.csv")
        sys.exit(1)
    
    slice_file = sys.argv[1]
    success = debug_slice_processing(slice_file)
    
    if not success:
        print("\n🚨 DIAGNÓSTICO INDICA PROBLEMAS CRÍTICOS!")
        print("   Verifique os logs acima para identificar a causa raiz.")
        sys.exit(1)
    else:
        print("\n✅ Diagnóstico concluído com sucesso!")

if __name__ == "__main__":
    main()
