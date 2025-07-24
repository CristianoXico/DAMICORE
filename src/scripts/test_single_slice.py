#!/usr/bin/env python3
"""
Teste de Fatia Individual
========================

Script para testar o processamento de uma única fatia e identificar
exatamente onde está ocorrendo a falha na geração dos arquivos newick.
"""

import os
import sys
import subprocess
import glob
import shutil
from pathlib import Path
from datetime import datetime

def test_slice_processing(slice_dir):
    """Testa o processamento de uma fatia específica"""
    
    print(f"🧪 Testando fatia: {slice_dir}")
    print("="*60)
    
    if not os.path.exists(slice_dir):
        print(f"❌ Diretório da fatia não existe: {slice_dir}")
        return False
    
    # Verifica arquivos de entrada
    csv_files = glob.glob(os.path.join(slice_dir, "*.csv"))
    if not csv_files:
        print(f"❌ Nenhum arquivo CSV encontrado na fatia")
        return False
    
    csv_file = csv_files[0]
    print(f"📄 Arquivo CSV: {os.path.basename(csv_file)}")
    
    # Verifica conteúdo do CSV
    try:
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        print(f"📊 Linhas no CSV: {len(lines)}")
        print(f"📊 Primeira linha (header): {lines[0].strip()[:100]}...")
        
        if len(lines) >= 2:
            print(f"📊 Segunda linha (dados): {lines[1].strip()[:100]}...")
        
        if len(lines) < 2:
            print(f"❌ CSV tem dados insuficientes para processamento")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return False
    
    # Localiza o script DAMICORE_Filograma_script.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filograma_script = os.path.join(script_dir, "DAMICORE_Filograma_script.py")
    
    if not os.path.exists(filograma_script):
        print(f"❌ Script DAMICORE_Filograma_script.py não encontrado: {filograma_script}")
        return False
    
    print(f"🔧 Script encontrado: {filograma_script}")
    
    # Backup dos arquivos existentes (se houver)
    backup_dir = os.path.join(slice_dir, "backup_before_test")
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    
    existing_newicks = glob.glob(os.path.join(slice_dir, "**/*.newick"), recursive=True)
    if existing_newicks:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"💾 Fazendo backup de {len(existing_newicks)} arquivos newick existentes")
        for newick_file in existing_newicks:
            rel_path = os.path.relpath(newick_file, slice_dir)
            backup_path = os.path.join(backup_dir, rel_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(newick_file, backup_path)
    
    # Executa o processamento
    print(f"\n🚀 Iniciando processamento da fatia...")
    print(f"🕐 Início: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        cmd = [sys.executable, filograma_script, csv_file]
        print(f"📝 Comando: {' '.join(cmd)}")
        
        # Executa com timeout de 10 minutos
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=slice_dir
        )
        
        stdout, stderr = process.communicate(timeout=600)  # 10 minutos
        
        print(f"🏁 Processamento concluído")
        print(f"🕐 Fim: {datetime.now().strftime('%H:%M:%S')}")
        print(f"📤 Código de saída: {process.returncode}")
        
        # Mostra saída do processo
        if stdout:
            print(f"\n📝 Saída padrão:")
            print("-" * 40)
            print(stdout)
            print("-" * 40)
        
        if stderr:
            print(f"\n⚠️ Saída de erro:")
            print("-" * 40)
            print(stderr)
            print("-" * 40)
        
        # Verifica arquivos gerados
        print(f"\n🔍 Verificando arquivos gerados...")
        
        new_newicks = glob.glob(os.path.join(slice_dir, "**/*.newick"), recursive=True)
        print(f"🎯 Arquivos .newick encontrados: {len(new_newicks)}")
        
        if new_newicks:
            print(f"✅ Arquivos newick gerados com sucesso:")
            for newick_file in new_newicks[:5]:  # Mostra primeiros 5
                rel_path = os.path.relpath(newick_file, slice_dir)
                file_size = os.path.getsize(newick_file)
                print(f"   - {rel_path} ({file_size} bytes)")
                
                # Verifica conteúdo
                try:
                    with open(newick_file, 'r') as f:
                        content = f.read().strip()
                    
                    if content:
                        print(f"     ✅ Conteúdo válido ({len(content)} caracteres)")
                        # Mostra preview do conteúdo
                        preview = content[:100] + "..." if len(content) > 100 else content
                        print(f"     📝 Preview: {preview}")
                    else:
                        print(f"     ❌ Arquivo vazio")
                        
                except Exception as e:
                    print(f"     ❌ Erro ao ler: {e}")
            
            if len(new_newicks) > 5:
                print(f"   ... e mais {len(new_newicks) - 5} arquivos")
        else:
            print(f"❌ Nenhum arquivo .newick foi gerado!")
            
            # Verifica outros arquivos que podem ter sido gerados
            all_files = []
            for root, dirs, files in os.walk(slice_dir):
                for file in files:
                    if file != os.path.basename(csv_file):  # Ignora o CSV original
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, slice_dir)
                        file_size = os.path.getsize(file_path)
                        all_files.append((rel_path, file_size))
            
            if all_files:
                print(f"📄 Outros arquivos gerados:")
                for file_path, file_size in sorted(all_files)[:10]:
                    print(f"   - {file_path} ({file_size} bytes)")
            else:
                print(f"📄 Nenhum arquivo adicional foi gerado")
        
        return process.returncode == 0 and len(new_newicks) > 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Processamento expirou após 10 minutos")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        return False

def main():
    """Função principal"""
    
    if len(sys.argv) < 2:
        print("Uso: python test_single_slice.py <caminho_da_fatia>")
        print("\nExemplo:")
        print("python test_single_slice.py /path/to/results/slice_0")
        return
    
    slice_dir = sys.argv[1]
    
    print(f"🧪 Teste de Fatia Individual - DAMICORE")
    print(f"🕐 Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_slice_processing(slice_dir)
    
    print(f"\n{'='*60}")
    if success:
        print(f"✅ SUCESSO: Fatia processada e arquivos newick gerados!")
    else:
        print(f"❌ FALHA: Fatia não gerou arquivos newick válidos")
        print(f"🔧 Verifique os logs acima para identificar o problema")
    
    print(f"🕐 Concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
