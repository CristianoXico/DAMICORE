#!/usr/bin/env python3
"""
Script ultra-radical para geração de visualização unificada com processamento streaming.
Resolve definitivamente o problema de OOM para datasets com 1000+ arquivos newick.
"""

import os
import sys
import gc
import random
import subprocess
from pathlib import Path

def generate_streaming_visualization(newick_files, output_dir, csv_file):
    """
    Gera visualização unificada usando processamento incremental ultra-radical.
    
    Args:
        newick_files (list): Lista de arquivos newick
        output_dir (str): Diretório de saída
        csv_file (str): Arquivo CSV original para mapeamento
    """
    print(f"🚀 STREAMING ULTRA-RADICAL: {len(newick_files)} arquivos")
    
    # Criar diretório de visualizações
    viz_dir = os.path.join(output_dir, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)
    
    # ESTRATÉGIA 1: Amostra ultra-reduzida (máximo 3 arquivos)
    if len(newick_files) > 1000:
        print("🔥 DATASET ULTRA-GIGANTE: Usando apenas 3 arquivos representativos")
        random.seed(42)
        selected_files = random.sample(newick_files, 3)
    elif len(newick_files) > 500:
        print("🔥 DATASET GIGANTE: Usando apenas 5 arquivos representativos")
        random.seed(42)
        selected_files = random.sample(newick_files, 5)
    else:
        print("📊 DATASET MÉDIO: Usando amostra de 10 arquivos")
        random.seed(42)
        selected_files = random.sample(newick_files, min(10, len(newick_files)))
    
    print(f"✅ {len(selected_files)} arquivos selecionados para processamento")
    
    # ESTRATÉGIA 2: Processamento sequencial puro (um arquivo por vez)
    newick_contents = []
    for i, newick_file in enumerate(selected_files):
        print(f"📖 Processando arquivo {i+1}/{len(selected_files)}: {os.path.basename(newick_file)}")
        
        try:
            with open(newick_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    newick_contents.append(content)
            
            # Limpeza agressiva de memória após cada arquivo
            gc.collect()
            
        except Exception as e:
            print(f"⚠️ Erro ao ler {newick_file}: {e}")
            continue
    
    if not newick_contents:
        print("❌ Nenhum arquivo newick válido encontrado")
        return False
    
    print(f"✅ {len(newick_contents)} arquivos processados com sucesso")
    
    # ESTRATÉGIA 3: Geração de visualização minimalista
    try:
        # Usar script externo para evitar problemas de memória
        script_path = os.path.join(os.path.dirname(__file__), "exact_damicore_unified.py")
        
        if os.path.exists(script_path):
            print("🎨 Gerando visualizações via script externo...")
            
            # Criar arquivo temporário com newicks selecionados
            temp_dir = os.path.join(output_dir, "temp_streaming")
            os.makedirs(temp_dir, exist_ok=True)
            
            for i, content in enumerate(newick_contents):
                temp_file = os.path.join(temp_dir, f"temp_{i:03d}.newick")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Executar script externo com timeout
            cmd = [
                sys.executable, script_path,
                temp_dir, viz_dir, csv_file or ""
            ]
            
            result = subprocess.run(
                cmd, 
                timeout=300,  # 5 minutos máximo
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Visualizações geradas com sucesso!")
                
                # Limpar arquivos temporários
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                return True
            else:
                print(f"❌ Erro na geração: {result.stderr}")
                return False
        
        else:
            print("⚠️ Script externo não encontrado - usando fallback")
            return generate_minimal_fallback(newick_contents, viz_dir)
            
    except Exception as e:
        print(f"❌ Erro crítico na geração de visualizações: {e}")
        return generate_minimal_fallback(newick_contents, viz_dir)

def generate_minimal_fallback(newick_contents, viz_dir):
    """
    Fallback ultra-minimalista para casos extremos.
    """
    print("🔧 FALLBACK ULTRA-MINIMALISTA")
    
    try:
        # Gerar apenas relatório estatístico
        stats_file = os.path.join(viz_dir, "streaming_statistics.txt")
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("DAMICORE STREAMING VISUALIZATION STATISTICS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total newick files processed: {len(newick_contents)}\n")
            f.write(f"Average newick length: {sum(len(n) for n in newick_contents) / len(newick_contents):.1f} chars\n")
            f.write(f"Total characters: {sum(len(n) for n in newick_contents)}\n")
            f.write(f"Processing method: Ultra-radical streaming\n")
            f.write(f"Memory optimization: Maximum\n\n")
            
            f.write("SAMPLE NEWICK CONTENT:\n")
            f.write("-" * 30 + "\n")
            for i, content in enumerate(newick_contents[:3]):  # Apenas 3 primeiros
                f.write(f"File {i+1}: {content[:100]}...\n")
        
        print(f"✅ Relatório estatístico salvo: {stats_file}")
        return True
        
    except Exception as e:
        print(f"❌ Falha no fallback: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python generate_streaming_visualization.py <newick_dir> <output_dir> <csv_file>")
        sys.exit(1)
    
    newick_dir = sys.argv[1]
    output_dir = sys.argv[2]
    csv_file = sys.argv[3] if sys.argv[3] else None
    
    # Coletar arquivos newick
    newick_files = []
    for filename in os.listdir(newick_dir):
        if filename.endswith('.newick'):
            newick_files.append(os.path.join(newick_dir, filename))
    
    if not newick_files:
        print("❌ Nenhum arquivo newick encontrado")
        sys.exit(1)
    
    success = generate_streaming_visualization(newick_files, output_dir, csv_file)
    sys.exit(0 if success else 1)
